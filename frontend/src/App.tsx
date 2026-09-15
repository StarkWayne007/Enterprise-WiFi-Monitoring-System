import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js"
import { Bar, Doughnut, Line } from "react-chartjs-2"
import { useEffect, useMemo, useRef, useState } from "react"
import type { FormEvent } from "react"
import "./App.css"

const API = "http://127.0.0.1:8000"

type Device = {
  id: number
  mac_address: string
  ip_address: string | null
  hostname: string | null
  vendor: string | null
  device_type: string | null
  first_seen?: string
  last_seen?: string
}

type Usage = {
  device_mac: string
  total_bytes: number
}

type Behavior = {
  device_mac: string
  event_count: number
  total_bytes: number
  unique_destinations?: number
  bytes_per_second?: number
  status: string
}

type Alert = {
  id: number
  device_mac: string | null
  alert_type: string
  severity: string
  description: string
  status?: string
  created_at: string
}

type TelemetryEvent = {
  id: number
  timestamp: string
  event_type: string
  source: string
  device_mac: string | null
  ip_address: string | null
  destination_ip: string | null
  protocol: string | null
  bytes_transferred: number
  created_at: string
}

type TrafficPoint = {
  timestamp: string
  bytes_transferred: number
}

type TrafficHistory = {
  traffic_limit_bytes: number
  data: TrafficPoint[]
}

type ReportSummary = {
  device_count: number
  traffic_event_count: number
  total_bytes: number
  alert_count: number
  unresolved_alert_count: number
}

type NewDevice = {
  hostname: string
  ip_address: string
  mac_address: string
  vendor: string
  device_type: string
}

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Filler,
)

const formatBytes = (bytes: number) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B"

  const units = ["B", "KB", "MB", "GB", "TB"]
  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  )

  return `${(bytes / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`
}

const formatNumber = (value: number) =>
  new Intl.NumberFormat("en-US").format(value)

const formatTime = (value: string) =>
  new Date(value).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })

const formatDateTime = (value: string) =>
  new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  })

const shortMac = (mac: string | null) => {
  if (!mac) return "Unknown device"
  return mac.toUpperCase()
}

function App() {
  const [devices, setDevices] = useState<Device[]>([])
  const [usage, setUsage] = useState<Usage[]>([])
  const [behavior, setBehavior] = useState<Behavior[]>([])
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [events, setEvents] = useState<TelemetryEvent[]>([])
  const [trafficHistory, setTrafficHistory] = useState<TrafficHistory>({
    traffic_limit_bytes: 0,
    data: [],
  })
  const [reportSummary, setReportSummary] = useState<ReportSummary>({
    device_count: 0,
    traffic_event_count: 0,
    total_bytes: 0,
    alert_count: 0,
    unresolved_alert_count: 0,
  })

  const [showAddDevice, setShowAddDevice] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState("")
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [activeSection, setActiveSection] = useState("overview")
  const [newEventCount, setNewEventCount] = useState(0)
  const knownEventIds = useRef<Set<number> | null>(null)

  const [settings, setSettings] = useState({
    traffic_limit_bytes: 0,
    behavior_window_minutes: 1440,
    event_frequency_limit: 100,
    technician_email: "",
    interface: "eth0",
    packet_count: 10,
    interval_seconds: 2,
  })
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsMessage, setSettingsMessage] = useState("")
  const [settingsError, setSettingsError] = useState("")

  const [newDevice, setNewDevice] = useState<NewDevice>({
    hostname: "",
    ip_address: "",
    mac_address: "",
    vendor: "",
    device_type: "Laptop",
  })

  const loadSettings = async () => {
    try {
      const responses = await Promise.all([
        fetch(`${API}/settings/traffic-limit`),
        fetch(`${API}/settings/behavior-window`),
        fetch(`${API}/settings/event-frequency`),
        fetch(`${API}/settings/capture`),
        fetch(`${API}/settings/technician-email`),
      ])

      const [traffic, behaviorWindow, eventFrequency, capture] =
        await Promise.all(
          responses.slice(0, 4).map((response) => {
            if (!response.ok) throw new Error("Unable to load system settings.")
            return response.json()
          }),
        )

      let technicianEmail = ""
      if (responses[4].ok) {
        const data = await responses[4].json()
        technicianEmail = data.technician_email
      }

      setSettings({
        traffic_limit_bytes: traffic.traffic_limit_bytes,
        behavior_window_minutes: behaviorWindow.behavior_window_minutes,
        event_frequency_limit: eventFrequency.event_frequency_limit,
        technician_email: technicianEmail,
        interface: capture.interface,
        packet_count: capture.packet_count,
        interval_seconds: capture.interval_seconds,
      })
    } catch (err) {
      setSettingsError(
        err instanceof Error ? err.message : "Unable to load system settings.",
      )
    }
  }

  const saveSettings = async (event: FormEvent) => {
    event.preventDefault()
    setSettingsSaving(true)
    setSettingsMessage("")
    setSettingsError("")

    try {
      const requests = [
        fetch(`${API}/settings/traffic-limit`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            traffic_limit_bytes: settings.traffic_limit_bytes,
          }),
        }),
        fetch(`${API}/settings/behavior-window`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            behavior_window_minutes: settings.behavior_window_minutes,
          }),
        }),
        fetch(`${API}/settings/event-frequency`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            event_frequency_limit: settings.event_frequency_limit,
          }),
        }),
        fetch(`${API}/settings/capture`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            interface: settings.interface,
            packet_count: settings.packet_count,
            interval_seconds: settings.interval_seconds,
          }),
        }),
        fetch(`${API}/settings/technician-email`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            technician_email: settings.technician_email,
          }),
        }),
      ]

      const responses = await Promise.all(requests)
      const failed = responses.find((response) => !response.ok)

      if (failed) {
        const body = await failed.json().catch(() => null)
        throw new Error(body?.detail || "Failed to save one or more settings.")
      }

      setSettingsMessage("Settings saved successfully.")
      await loadDashboard()
    } catch (err) {
      setSettingsError(
        err instanceof Error ? err.message : "Failed to save settings.",
      )
    } finally {
      setSettingsSaving(false)
    }
  }

  const loadDashboard = async (manual = false) => {
    if (manual) setRefreshing(true)
    setError("")

    try {
      const [
        devicesResponse,
        usageResponse,
        behaviorResponse,
        alertsResponse,
        eventsResponse,
        historyResponse,
        summaryResponse,
      ] = await Promise.all([
        fetch(`${API}/devices/`),
        fetch(`${API}/usage/devices`),
        fetch(`${API}/behavior/devices`),
        fetch(`${API}/alerts/`),
        fetch(`${API}/telemetry/events`),
        fetch(`${API}/telemetry/traffic-history?minutes=1440`),
        fetch(`${API}/reports/summary`),
      ])

      const responses = [
        devicesResponse,
        usageResponse,
        behaviorResponse,
        alertsResponse,
        eventsResponse,
        historyResponse,
        summaryResponse,
      ]

      if (responses.some((response) => !response.ok)) {
        throw new Error("One or more backend services returned an error.")
      }

      const [
        devicesData,
        usageData,
        behaviorData,
        alertsData,
        eventsData,
        historyData,
        summaryData,
      ] = await Promise.all(responses.map((response) => response.json()))

      setDevices(devicesData)
      setUsage(usageData)
      setBehavior(behaviorData)
      setAlerts(alertsData)

      const incomingEventIds = new Set<number>(
        eventsData.map((event: TelemetryEvent) => event.id),
      )

      if (knownEventIds.current === null) {
        knownEventIds.current = incomingEventIds
        setNewEventCount(0)
      } else {
        const freshEvents = eventsData.filter(
          (event: TelemetryEvent) => !knownEventIds.current!.has(event.id),
        )

        if (freshEvents.length > 0) {
          setNewEventCount((count) => count + freshEvents.length)
        }

        knownEventIds.current = new Set([
          ...knownEventIds.current,
          ...incomingEventIds,
        ])
      }

      setEvents(eventsData)
      setTrafficHistory(historyData)
      setReportSummary(summaryData)
      setLastUpdated(new Date())
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect to the monitoring backend.",
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadDashboard()
    loadSettings()

    const interval = window.setInterval(() => {
      loadDashboard()
    }, 3000)

    return () => window.clearInterval(interval)
  }, [])

  useEffect(() => {
    const ids = ["overview", "analytics", "devices", "alerts", "events", "reports", "settings"]
    const sections = ids
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => Boolean(section))

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)

        if (visible[0]?.target.id) {
          setActiveSection(visible[0].target.id)
        }
      },
      {
        rootMargin: "-88px 0px -55% 0px",
        threshold: [0.1, 0.25, 0.5],
      },
    )

    sections.forEach((section) => observer.observe(section))
    return () => observer.disconnect()
  }, [])

  const usageMap = useMemo(() => {
    return new Map(
      usage.map((item) => [item.device_mac.toUpperCase(), item.total_bytes]),
    )
  }, [usage])

  const behaviorMap = useMemo(() => {
    return new Map(
      behavior.map((item) => [item.device_mac.toUpperCase(), item]),
    )
  }, [behavior])

  const deviceName = (mac: string | null) => {
    if (!mac) return "Unknown device"

    const device = devices.find(
      (item) => item.mac_address.toUpperCase() === mac.toUpperCase(),
    )

    return device?.hostname || mac
  }

  const observedMacs = useMemo(() => {
    const set = new Set<string>()

    usage.forEach((item) => set.add(item.device_mac.toUpperCase()))
    behavior.forEach((item) => set.add(item.device_mac.toUpperCase()))

    events.forEach((event) => {
      if (event.device_mac) {
        set.add(event.device_mac.toUpperCase())
      }
    })

    devices.forEach((device) => set.add(device.mac_address.toUpperCase()))

    return Array.from(set)
  }, [devices, usage, behavior, events])

  const observedIpMap = useMemo(() => {
    const map = new Map<string, string>()
    events
      .slice()
      .sort(
        (a, b) =>
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
      )
      .forEach((event) => {
        if (event.device_mac && event.ip_address) {
          const mac = event.device_mac.toUpperCase()
          if (!map.has(mac)) map.set(mac, event.ip_address)
        }
      })
    return map
  }, [events])

  const unknownObservedMacs = useMemo(() => {
    const registered = new Set(
      devices.map((device) => device.mac_address.toUpperCase()),
    )
    return observedMacs.filter((mac) => !registered.has(mac))
  }, [observedMacs, devices])

  const addObservedClient = (mac: string) => {
    setNewDevice({
      hostname: "",
      ip_address: observedIpMap.get(mac) ?? "",
      mac_address: mac,
      vendor: "",
      device_type: "Other",
    })
    setShowAddDevice(true)
    scrollTo("devices")
  }

  const normalDevices = behavior.filter(
    (item) => item.status === "normal",
  ).length

  const suspiciousDevices = behavior.filter(
    (item) => item.status === "suspicious",
  ).length

  const activeAlerts = alerts.filter(
    (alert) => alert.status !== "resolved",
  ).length

  const trafficToday = reportSummary.total_bytes

  const trafficChartRows = useMemo(() => {
    return observedMacs
      .map((mac) => ({
        mac,
        name: deviceName(mac),
        bytes: usageMap.get(mac) ?? 0,
      }))
      .sort((a, b) => b.bytes - a.bytes)
      .slice(0, 8)
  }, [observedMacs, usageMap, devices])

  const trafficBarData = {
    labels: trafficChartRows.map((item) => item.name),
    datasets: [
      {
        label: "Traffic",
        data: trafficChartRows.map((item) => item.bytes),
        backgroundColor: "#2997FF",
        borderColor: "#2997FF",
        borderRadius: 8,
        borderSkipped: false,
      },
    ],
  }

  const trafficLineData = {
    labels: trafficHistory.data.map((point) =>
      formatTime(point.timestamp),
    ),

    datasets: [
      {
        label: "Network Traffic",

        data: trafficHistory.data.map(
          (point) => point.bytes_transferred,
        ),

        borderColor: (context: any) => {
          const chart = context.chart
          const { ctx, chartArea } = chart

          if (!chartArea) {
            return "#2997FF"
          }

          const gradient = ctx.createLinearGradient(
            0,
            chartArea.bottom,
            0,
            chartArea.top,
          )

          gradient.addColorStop(0, "#2997FF")
          gradient.addColorStop(0.25, "#22D3EE")
          gradient.addColorStop(0.45, "#22D3A0")
          gradient.addColorStop(0.65, "#FACC15")
          gradient.addColorStop(0.82, "#FB923C")
          gradient.addColorStop(1, "#FF4D61")

          return gradient
        },

        backgroundColor: (context: any) => {
          const chart = context.chart
          const { ctx, chartArea } = chart

          if (!chartArea) {
            return "rgba(41, 151, 255, 0.08)"
          }

          const gradient = ctx.createLinearGradient(
            0,
            chartArea.bottom,
            0,
            chartArea.top,
          )

          gradient.addColorStop(
            0,
            "rgba(41, 151, 255, 0.10)",
          )

          gradient.addColorStop(
            0.45,
            "rgba(34, 211, 160, 0.08)",
          )

          gradient.addColorStop(
            0.7,
            "rgba(250, 204, 21, 0.08)",
          )

          gradient.addColorStop(
            1,
            "rgba(255, 77, 97, 0.12)",
          )

          return gradient
        },

        pointBackgroundColor: (context: any) => {
          const value = Number(context.raw ?? 0)
          const threshold =
            trafficHistory.traffic_limit_bytes || 1000

          if (value >= threshold * 3) {
            return "#FF4D61"
          }

          if (value >= threshold * 2) {
            return "#FB923C"
          }

          if (value >= threshold) {
            return "#FACC15"
          }

          if (value >= threshold * 0.5) {
            return "#22D3A0"
          }

          return "#2997FF"
        },

        pointBorderColor: "#07101C",
        pointHoverBackgroundColor: "#FFFFFF",
        pointHoverBorderColor: "#FFFFFF",

        fill: true,
        tension: 0.35,

        pointRadius: 2,
        pointHoverRadius: 5,

        borderWidth: 2,

        spanGaps: true,
      },

      {
        label: "Threshold",

        data: trafficHistory.data.map(
          () => trafficHistory.traffic_limit_bytes,
        ),

        borderColor: "#FF4D61",
        borderDash: [8, 6],
        borderWidth: 1.5,

        pointRadius: 0,
        pointHoverRadius: 0,

        fill: false,
        tension: 0,

        spanGaps: true,
      },
    ],
  }

  const deviceTypes = useMemo(() => {
    const counts = new Map<string, number>()

    devices.forEach((device) => {
      const type = device.device_type || "Unknown"
      counts.set(type, (counts.get(type) ?? 0) + 1)
    })

    return Array.from(counts.entries())
  }, [devices])


const deviceTypeChartData = {
  labels: deviceTypes.map(([type]) => type),

  datasets: [
    {
      data: deviceTypes.map(([, count]) => count),

      backgroundColor: [
        "#2997FF",
        "#8B5CF6",
        "#22D3EE",
        "#F59E0B",
        "#20D6A0",
        "#667085",
      ],

      hoverBackgroundColor: [
        "#50AAFF",
        "#A78BFA",
        "#67E8F9",
        "#FBBF24",
        "#34E6B0",
        "#98A2B3",
      ],

      borderWidth: 0,
    },
  ],
}


  const behaviorChartData = {
    labels: ["Normal", "Suspicious"],
    datasets: [
      {
        data: [normalDevices, suspiciousDevices],
        backgroundColor: ["#20D6A0", "#FF4D61"],
        hoverBackgroundColor: ["#34E6B0", "#FF6879"],
        borderWidth: 0,
      },
    ],
  }

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
      legend: {
        display: false,
      },
    },

    scales: {
      x: {
        grid: {
          display: false,
        },

        ticks: {
          color: "#A7B0C0",
        },
      },

      y: {
        grid: {
          color: "rgba(125, 155, 190, 0.12)",
        },

        ticks: {
          color: "#A7B0C0",
        },
      },
    },
  }

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,

    animation: false as const,

    interaction: {
      mode: "index" as const,
      intersect: false,
    },

    plugins: {
      legend: {
        display: false,
      },

      tooltip: {
        enabled: true,

        backgroundColor: "#111722",
        borderColor: "rgba(255, 255, 255, 0.10)",
        borderWidth: 1,

        titleColor: "#FFFFFF",
        bodyColor: "#A7B0C0",

        padding: 12,

        displayColors: false,

        callbacks: {
          label: (context: any) => {
            const value = Number(context.raw ?? 0)

            return `Traffic: ${formatBytes(value)}`
          },
        },
      },
    },

    scales: {
      x: {
        grid: {
          color: "rgba(255, 255, 255, 0.05)",
        },

        ticks: {
          color: "#7F8A9A",
          maxTicksLimit: 8,
          autoSkip: true,
        },
      },

      y: {
        beginAtZero: true,

        max: Math.max(
          trafficHistory.traffic_limit_bytes * 5,
          8000,
        ),

        grid: {
          color: "rgba(255, 255, 255, 0.05)",
        },

        ticks: {
          color: "#7F8A9A",

          callback: (value: string | number) => {
            return formatBytes(Number(value))
          },
        },
      },
    },
  }


  const addDevice = async (event: FormEvent) => {
    event.preventDefault()

    try {
      const response = await fetch(`${API}/devices/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newDevice),
      })

      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail || "Failed to add device.")
      }

      setNewDevice({
        hostname: "",
        ip_address: "",
        mac_address: "",
        vendor: "",
        device_type: "Laptop",
      })

      setShowAddDevice(false)
      await loadDashboard()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to add device.")
    }
  }

  const removeDevice = async (device: Device) => {
    const name = device.hostname || device.mac_address

    if (!window.confirm(`Remove ${name}?`)) return

    try {
      const response = await fetch(`${API}/devices/${device.id}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        throw new Error("Failed to remove device.")
      }

      await loadDashboard()
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to remove device.")
    }
  }

  const scrollTo = (id: string) => {
    const target = document.getElementById(id)
    if (!target) return

    setActiveSection(id)

    const topbarOffset = 96
    const top = target.getBoundingClientRect().top + window.scrollY - topbarOffset

    window.scrollTo({
      top: Math.max(0, top),
      behavior: "smooth",
    })
  }

  const severityClass = (severity: string) => {
    const value = severity.toLowerCase()

    if (value === "high" || value === "critical") return "danger"
    if (value === "medium") return "warning"
    return "info"
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo">NW</div>
        <div>
          <h2>NetWatch</h2>
          <p>Connecting to monitoring services...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <span>⌁</span>
          </div>
          <div>
            <strong>NetWatch</strong>
            <small>Wi-Fi Monitoring & Analytics</small>
          </div>
        </div>

        <nav className="side-nav">
          <button className={`nav-item ${activeSection === "overview" ? "active" : ""}`} onClick={() => scrollTo("overview")}>
            <span>⌂</span>
            Overview
          </button>
          <button className={`nav-item ${activeSection === "analytics" ? "active" : ""}`} onClick={() => scrollTo("analytics")}>
            <span>◌</span>
            Analytics
          </button>
          <button className={`nav-item ${activeSection === "devices" ? "active" : ""}`} onClick={() => scrollTo("devices")}>
            <span>▦</span>
            Devices
          </button>
          <button className={`nav-item ${activeSection === "alerts" ? "active" : ""}`} onClick={() => scrollTo("alerts")}>
            <span>△</span>
            Security
          </button>
          <button className={`nav-item ${activeSection === "events" ? "active" : ""}`} onClick={() => scrollTo("events")}>
            <span>≋</span>
            Events
          </button>
          <button className={`nav-item ${activeSection === "reports" ? "active" : ""}`} onClick={() => scrollTo("reports")}>
            <span>▤</span>
            Reports
          </button>
          <button className={`nav-item ${activeSection === "settings" ? "active" : ""}`} onClick={() => scrollTo("settings")}>
            <span>⚙</span>
            Settings
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-mini">
            <span className="status-dot online" />
            <div>
              <strong>Monitoring online</strong>
              <small>Backend connected</small>
            </div>
          </div>

          <div className="sidebar-footer">
            <span>NetWatch</span>
            <span>v1.0</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="mobile-brand">
            <div className="brand-icon small">NW</div>
            <strong>NetWatch</strong>
          </div>

          <div className="topbar-title">
            <span>NETWORK OPERATIONS</span>
            <strong>Enterprise Wi-Fi Monitor</strong>
          </div>

          <div className="topbar-actions">
            <div className="search-box">
              <span>⌕</span>
              <input placeholder="Search network..." />
            </div>

            <button
              className={`icon-button ${refreshing ? "spinning" : ""}`}
              onClick={() => loadDashboard(true)}
              title="Refresh"
            >
              ↻
            </button>

            <div className="user-chip">
              <div className="avatar">A</div>
              <div className="user-details">
                <strong>Admin</strong>
                <small>Administrator</small>
              </div>
            </div>
          </div>
        </header>

        {error && (
          <div className="error-banner">
            <span>⚠</span>
            <div>
              <strong>Backend connection issue</strong>
              <p>{error}</p>
            </div>
            <button onClick={() => loadDashboard(true)}>Retry</button>
          </div>
        )}

        <section id="overview" className="hero-section">
          <div className="hero-copy">
            <span className="eyebrow">NETWORK OBSERVABILITY</span>
            <h1>
              Monitor.
              <br />
              Understand.
              <br />
              Stay Connected.
            </h1>
            <p>
              Real-time Wi-Fi usage, device activity and network behaviour
              analysis — in one place.
            </p>

            <div className="hero-actions">
              <button className="primary-button" onClick={() => scrollTo("analytics")}>
                View Live Traffic <span>→</span>
              </button>
              <button className="secondary-button" onClick={() => scrollTo("reports")}>
                Generate Report
              </button>
            </div>
          </div>

          <div className="network-visual">
            <div className="radar-ring ring-one" />
            <div className="radar-ring ring-two" />
            <div className="radar-ring ring-three" />
            <div className="router">
              <div className="router-top">
                <span />
                <span />
                <span />
                <span />
                <span />
              </div>
              <div className="antenna left" />
              <div className="antenna right" />
            </div>
            <div className="network-lines" />
          </div>

          <div className="hero-status">
            <div className="status-card">
              <div className="status-icon online">✓</div>
              <div>
                <small>Network Status</small>
                <strong>Online</strong>
                <span>All systems operational</span>
              </div>
              <b>›</b>
            </div>

            <div className="status-card">
              <div className={`status-icon ${activeAlerts ? "danger" : "online"}`}>
                {activeAlerts || "✓"}
              </div>
              <div>
                <small>Active Alerts</small>
                <strong>{activeAlerts}</strong>
                <span>{activeAlerts ? "Requires attention" : "No action required"}</span>
              </div>
              <b>›</b>
            </div>
          </div>
        </section>

        <section className="stat-grid">
          <div className="stat-card">
            <div className="stat-icon blue">⌘</div>
            <div>
              <span>Total Devices</span>
              <strong>{reportSummary.device_count}</strong>
              <small>Registered devices</small>
            </div>
            <div className="stat-decoration">01</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon violet">●</div>
            <div>
              <span>Observed Clients</span>
              <strong>{observedMacs.length}</strong>
              <small>From telemetry</small>
            </div>
            <div className="stat-decoration">02</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon cyan">◈</div>
            <div>
              <span>Data Processed</span>
              <strong>{formatBytes(trafficToday)}</strong>
              <small>{formatNumber(reportSummary.traffic_event_count)} traffic events</small>
            </div>
            <div className="stat-decoration">03</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon red">!</div>
            <div>
              <span>Security Alerts</span>
              <strong>{reportSummary.alert_count}</strong>
              <small>{reportSummary.unresolved_alert_count} unresolved</small>
            </div>
            <div className="stat-decoration">04</div>
          </div>
        </section>

        <section id="analytics" className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">TELEMETRY</span>
              <h2>Live Network Traffic</h2>
              <p>Recent traffic activity collected by the monitoring engine.</p>
            </div>

            <div className="section-live-status">
              <div className="live-pill">
                <span className="pulse-dot" />
                LIVE
              </div>

              {newEventCount > 0 && (
                <button
                  className="new-events-pill"
                  onClick={() => setNewEventCount(0)}
                  title="Clear new-event counter"
                >
                  +{newEventCount} new
                </button>
              )}
            </div>
          </div>

          <div className="traffic-panel glass-panel">
            <div className="traffic-side">
              <div className="traffic-metric">
                <span>Total Processed</span>
                <strong>{formatBytes(trafficToday)}</strong>
                <small>Current telemetry dataset</small>
              </div>

              <div className="traffic-metric">
                <span>Traffic Events</span>
                <strong>{formatNumber(reportSummary.traffic_event_count)}</strong>
                <small>Recorded events</small>
              </div>

              <div className="traffic-metric">
                <span>Threshold</span>
                <strong>{formatBytes(trafficHistory.traffic_limit_bytes)}</strong>
                <small>Behaviour traffic limit</small>
              </div>
            </div>

<div className="traffic-chart">
  {trafficHistory.data.length > 0 ? (
    <div className="traffic-chart-wrapper">

      {/* Custom traffic legend */}
      <div className="traffic-chart-legend">

        <div className="traffic-gradient-legend">
          <div className="traffic-gradient-bar" />

          <div className="traffic-gradient-labels">
            <span>Low Activity</span>
            <span>High Activity</span>
          </div>
        </div>

        <div className="traffic-threshold-legend">
          <span className="traffic-threshold-line" />

          <span>
            Threshold (
            {trafficHistory.traffic_limit_bytes.toLocaleString()}
            {" "}B)
          </span>
        </div>

      </div>

      {/* Live traffic chart */}
      <div className="traffic-chart-canvas">
        <Line
          data={trafficLineData}
          options={lineOptions}
        />
      </div>

    </div>
  ) : (
    <div className="empty-chart">
      <span>∿</span>

      <strong>
        No traffic history available
      </strong>

      <small>
        Traffic telemetry will appear here.
      </small>
    </div>
  )}
</div>
</div>





          <div className="analytics-grid">
            <div className="glass-panel chart-card">
              <div className="card-heading">
                <div>
                  <span className="eyebrow">USAGE</span>
                  <h3>Top Observed Clients by Traffic</h3>
                </div>
                <span className="mini-label">TOP 8 OBSERVED</span>
              </div>

              <div className="bar-chart">
                {trafficChartRows.length > 0 ? (
                  <Bar data={trafficBarData} options={chartOptions} />
                ) : (
                  <div className="empty-state">
                    <strong>No device traffic data</strong>
                    <span>Register devices or collect telemetry.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="glass-panel chart-card compact-chart">
              <div className="card-heading">
                <div>
                  <span className="eyebrow">INVENTORY</span>
                  <h3>Device Types</h3>
                </div>
              </div>

              <div className="donut-wrapper">
                {deviceTypes.length > 0 ? (
                  <>
                    <Doughnut
  data={deviceTypeChartData}
  options={{
    responsive: true,
    maintainAspectRatio: false,

    cutout: "65%",

    plugins: {
      legend: {
        position: "bottom",

        labels: {
          color: "#aab2c1",
          padding: 8,
          boxWidth: 38,
          boxHeight: 10,
          font: {
            size: 11,
          },
        },
      },
    },
  }}
/>
                    <div className="donut-center">
                      <strong>{devices.length}</strong>
                      <span>devices</span>
                    </div>
                  </>
                ) : (
                  <div className="empty-state">
                    <strong>No inventory yet</strong>
                    <span>Add devices to populate this chart.</span>
                  </div>
                )}
              </div>
            </div>

            <div className="glass-panel chart-card compact-chart">
              <div className="card-heading">
                <div>
                  <span className="eyebrow">BEHAVIOUR</span>
                  <h3>Behaviour Status</h3>
                </div>
              </div>

              <div className="behavior-summary">
                <div className="behavior-stat normal">
                  <span className="behavior-stat-dot" />
                  <div>
                    <strong>{normalDevices}</strong>
                    <small>Normal</small>
                  </div>
                </div>

                <div className="behavior-stat suspicious">
                  <span className="behavior-stat-dot" />
                  <div>
                    <strong>{suspiciousDevices}</strong>
                    <small>Suspicious</small>
                  </div>
                </div>

                <div className="behavior-window">
                  <span>Analysis window</span>
                  <strong>24 hours</strong>
                </div>
              </div>

              <div className="behavior-visual">
                {behavior.length > 0 ? (
                  <>
                    <Doughnut
                      data={behaviorChartData}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: "70%",

                        layout: {
                          padding: {
                           top: 4,
                           bottom: 0,
                          },
                        },
                        plugins: {
                          legend: {
                            position: "bottom",
                            labels: {
                              color: "#aab2c1",
                              padding: 14,
                              boxWidth: 38,
                              boxHeight: 10,
                              font: {
                                size: 11,
                            },
                            },
                          },
                        },
                      }}
                    />
                    <div className="donut-center">
                      <strong>{behavior.length}</strong>
                      <span>analysed</span>
                    </div>
                  </>
                ) : (
                  <div className="empty-state compact-empty">
                    <strong>No recent behaviour data</strong>
                    <span>
                      Behaviour analysis uses the rolling 24-hour telemetry
                      window. Fresh traffic will populate this panel.
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section id="devices" className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">INVENTORY</span>
              <h2>Network Devices</h2>
              <p>Registered devices and their observed network behaviour.</p>
            </div>

            <button
              className="primary-button"
              onClick={() => setShowAddDevice(!showAddDevice)}
            >
              {showAddDevice ? "Close Form" : "+ Add Device"}
            </button>
          </div>

          {showAddDevice && (
            <form className="glass-panel add-device-panel" onSubmit={addDevice}>
              <div className="form-heading">
                <div>
                  <span className="eyebrow">DEVICE REGISTRATION</span>
                  <h3>Add Network Device</h3>
                </div>
              </div>

              <div className="form-grid">
                <input
                  required
                  placeholder="Hostname"
                  value={newDevice.hostname}
                  onChange={(event) =>
                    setNewDevice({
                      ...newDevice,
                      hostname: event.target.value,
                    })
                  }
                />

                <input
                  required
                  placeholder="IP Address"
                  value={newDevice.ip_address}
                  onChange={(event) =>
                    setNewDevice({
                      ...newDevice,
                      ip_address: event.target.value,
                    })
                  }
                />

                <input
                  required
                  placeholder="MAC Address"
                  value={newDevice.mac_address}
                  onChange={(event) =>
                    setNewDevice({
                      ...newDevice,
                      mac_address: event.target.value,
                    })
                  }
                />

                <input
                  placeholder="Vendor"
                  value={newDevice.vendor}
                  onChange={(event) =>
                    setNewDevice({
                      ...newDevice,
                      vendor: event.target.value,
                    })
                  }
                />

                <select
                  value={newDevice.device_type}
                  onChange={(event) =>
                    setNewDevice({
                      ...newDevice,
                      device_type: event.target.value,
                    })
                  }
                >
                  <option>Laptop</option>
                  <option>Desktop</option>
                  <option>Smartphone</option>
                  <option>Tablet</option>
                  <option>Server</option>
                  <option>Router</option>
                  <option>Access Point</option>
                  <option>IoT Device</option>
                  <option>Other</option>
                </select>

                <button className="primary-button" type="submit">
                  Register Device
                </button>
              </div>
            </form>
          )}

          <div className="glass-panel observed-panel">
            <div className="card-heading">
              <div>
                <span className="eyebrow">TELEMETRY DISCOVERY</span>
                <h3>Observed Clients</h3>
              </div>
              <span className="mini-label">{unknownObservedMacs.length} NOT IN INVENTORY</span>
            </div>

            {unknownObservedMacs.length === 0 ? (
              <div className="observed-empty">
                <strong>No unregistered observed clients</strong>
                <span>All currently observed clients are already in inventory.</span>
              </div>
            ) : (
              <div className="observed-list">
                {unknownObservedMacs.map((mac) => (
                  <div className="observed-client" key={mac}>
                    <div className="observed-client-main">
                      <div className="device-avatar">?</div>
                      <div>
                        <strong>{shortMac(mac)}</strong>
                        <small>
                          {observedIpMap.get(mac) || "IP not observed"}
                        </small>
                      </div>
                    </div>
                    <button
                      className="secondary-button small-button"
                      onClick={() => addObservedClient(mac)}
                    >
                      + Add to Inventory
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="glass-panel table-panel">
            {devices.length === 0 ? (
              <div className="large-empty">
                <div className="empty-icon">⌁</div>
                <h3>No registered devices</h3>
                <p>
                  The backend currently has no device records. Telemetry can
                  still be analysed independently.
                </p>
                <button
                  className="secondary-button"
                  onClick={() => setShowAddDevice(true)}
                >
                  Register First Device
                </button>
              </div>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Device</th>
                      <th>IP Address</th>
                      <th>Type</th>
                      <th>Vendor</th>
                      <th>Traffic</th>
                      <th>Events</th>
                      <th>Behaviour</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {devices.map((device) => {
                      const mac = device.mac_address.toUpperCase()
                      const deviceBehavior = behaviorMap.get(mac)
                      const deviceUsage = usageMap.get(mac) ?? 0

                      return (
                        <tr key={device.id}>
                          <td>
                            <div className="device-cell">
                              <div className="device-avatar">
                                {device.device_type?.[0] || "D"}
                              </div>
                              <div>
                                <strong>{device.hostname || "Unnamed device"}</strong>
                                <small>{shortMac(device.mac_address)}</small>
                              </div>
                            </div>
                          </td>
                          <td>{device.ip_address || "—"}</td>
                          <td>{device.device_type || "Unknown"}</td>
                          <td>{device.vendor || "Unknown"}</td>
                          <td className="strong-cell">{formatBytes(deviceUsage)}</td>
                          <td>{deviceBehavior?.event_count ?? 0}</td>
                          <td>
                            <span
                              className={`status-badge ${
                                deviceBehavior?.status === "suspicious"
                                  ? "danger"
                                  : "success"
                              }`}
                            >
                              <span />
                              {deviceBehavior?.status || "No data"}
                            </span>
                          </td>
                          <td>
                            <button
                              className="table-action danger-action"
                              onClick={() => removeDevice(device)}
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        <section id="alerts" className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">SECURITY MONITORING</span>
              <h2>Security Alerts</h2>
              <p>Rule-based detections generated by the monitoring engine.</p>
            </div>

            <div className="alert-counter">
              <span>{activeAlerts}</span>
              unresolved
            </div>
          </div>

          <div className="alert-grid">
            {alerts.length === 0 ? (
              <div className="glass-panel large-empty">
                <div className="empty-icon success-icon">✓</div>
                <h3>No security alerts</h3>
                <p>The detection engine has not reported any alerts.</p>
              </div>
            ) : (
              alerts.slice(0, 8).map((alert) => (
                <div className="glass-panel alert-card" key={alert.id}>
                  <div className={`alert-icon ${severityClass(alert.severity)}`}>
                    {alert.severity.toLowerCase() === "high" ||
                    alert.severity.toLowerCase() === "critical"
                      ? "!"
                      : "△"}
                  </div>

                  <div className="alert-content">
                    <div className="alert-topline">
                      <span className={`severity ${severityClass(alert.severity)}`}>
                        {alert.severity}
                      </span>
                      <span>{formatDateTime(alert.created_at)}</span>
                    </div>

                    <h3>{alert.alert_type.replaceAll("_", " ")}</h3>
                    <p>{alert.description}</p>

                    <div className="alert-meta">
                      <span>Device</span>
                      <strong>{shortMac(alert.device_mac)}</strong>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>

        <section id="events" className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">EVENT STREAM</span>
              <h2>Recent Telemetry</h2>
              <p>Latest events received by the monitoring backend.</p>
            </div>
          </div>

          <div className="glass-panel table-panel">
            {events.length === 0 ? (
              <div className="large-empty">
                <div className="empty-icon">≋</div>
                <h3>No telemetry events</h3>
                <p>Captured or simulated events will appear here.</p>
              </div>
            ) : (
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Event</th>
                      <th>Device</th>
                      <th>Source IP</th>
                      <th>Destination</th>
                      <th>Protocol</th>
                      <th>Bytes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {events
                      .slice()
                      .sort(
                        (a, b) =>
                          new Date(b.timestamp).getTime() -
                          new Date(a.timestamp).getTime(),
                      )
                      .slice(0, 30)
                      .map((event) => {
                        const isRecent =
                          Date.now() - new Date(event.timestamp).getTime() < 10000

                        return (
                          <tr
                            key={event.id}
                            style={
                              isRecent
                                ? {
                                    boxShadow: "inset 3px 0 0 #20D6A0",
                                    background: "rgba(32, 214, 160, 0.05)",
                                  }
                                : undefined
                            }
                          >
                            <td className="time-cell">
                              {formatDateTime(event.timestamp)}
                              {isRecent && (
                                <small
                                  style={{
                                    display: "block",
                                    marginTop: "3px",
                                    color: "#20D6A0",
                                    fontSize: "10px",
                                    fontWeight: 700,
                                    letterSpacing: "0.08em",
                                  }}
                                >
                                  JUST NOW
                                </small>
                              )}
                            </td>
                          <td>
                            <span className="event-type">
                              {event.event_type}
                            </span>
                          </td>
                          <td>
                            <strong>{deviceName(event.device_mac)}</strong>
                            <small className="table-sub">
                              {event.device_mac || "Unidentified"}
                            </small>
                          </td>
                          <td>{event.ip_address || "—"}</td>
                          <td>{event.destination_ip || "—"}</td>
                          <td>
                            <span className="protocol-badge">
                              {event.protocol || "UNKNOWN"}
                            </span>
                          </td>
                          <td className="strong-cell">
                            {formatBytes(event.bytes_transferred)}
                          </td>
                          </tr>
                        )
                      })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        <section id="reports" className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">REPORTING</span>
              <h2>Network Report Summary</h2>
              <p>Current monitoring statistics available from the reporting service.</p>
            </div>
          </div>

          <div className="report-grid">
            <div className="glass-panel report-card">
              <span>Registered Devices</span>
              <strong>{reportSummary.device_count}</strong>
              <small>Device inventory records</small>
            </div>

            <div className="glass-panel report-card">
              <span>Traffic Events</span>
              <strong>{formatNumber(reportSummary.traffic_event_count)}</strong>
              <small>Processed telemetry events</small>
            </div>

            <div className="glass-panel report-card">
              <span>Total Traffic</span>
              <strong>{formatBytes(reportSummary.total_bytes)}</strong>
              <small>Across recorded traffic events</small>
            </div>

            <div className="glass-panel report-card">
              <span>Unresolved Alerts</span>
              <strong className={reportSummary.unresolved_alert_count ? "danger-text" : ""}>
                {reportSummary.unresolved_alert_count}
              </strong>
              <small>Require investigation or resolution</small>
            </div>
          </div>

          <div className="glass-panel report-banner">
            <div>
              <span className="eyebrow">SYSTEM STATUS</span>
              <h3>Monitoring engine operational</h3>
              <p>
                Data is being collected through the configured telemetry and
                packet-capture pipeline.
              </p>
            </div>

            <div className="report-status">
              <span className="status-dot online" />
              Online
            </div>
          </div>
        </section>

        <section id="settings" className="section-block">
          <div className="section-heading">
            <div>
              <span className="eyebrow">ADMINISTRATION</span>
              <h2>System Settings</h2>
              <p>Configure monitoring thresholds, packet capture and alert delivery.</p>
            </div>
          </div>

          <form className="glass-panel settings-panel" onSubmit={saveSettings}>
            <div className="settings-grid">
              <div className="setting-group">
                <label>Traffic Limit (bytes)</label>
                <input
                  type="number"
                  min="1"
                  value={settings.traffic_limit_bytes}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      traffic_limit_bytes: Number(event.target.value),
                    })
                  }
                />
                <small>Rolling traffic threshold used by detection.</small>
              </div>

              <div className="setting-group">
                <label>Behaviour Window (minutes)</label>
                <input
                  type="number"
                  min="1"
                  max="1440"
                  value={settings.behavior_window_minutes}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      behavior_window_minutes: Number(event.target.value),
                    })
                  }
                />
                <small>Maximum 1440 minutes (24 hours).</small>
              </div>

              <div className="setting-group">
                <label>Event Frequency Limit</label>
                <input
                  type="number"
                  min="1"
                  value={settings.event_frequency_limit}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      event_frequency_limit: Number(event.target.value),
                    })
                  }
                />
                <small>Traffic events permitted within the analysis window.</small>
              </div>

              <div className="setting-group">
                <label>Capture Interface</label>
                <input
                  value={settings.interface}
                  onChange={(event) =>
                    setSettings({ ...settings, interface: event.target.value })
                  }
                  placeholder="eth0"
                />
                <small>Network interface used by packet capture.</small>
              </div>

              <div className="setting-group">
                <label>Capture Packet Count</label>
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={settings.packet_count}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      packet_count: Number(event.target.value),
                    })
                  }
                />
                <small>Packets captured per capture cycle.</small>
              </div>

              <div className="setting-group">
                <label>Capture Interval (seconds)</label>
                <input
                  type="number"
                  min="1"
                  max="3600"
                  value={settings.interval_seconds}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      interval_seconds: Number(event.target.value),
                    })
                  }
                />
                <small>Delay between capture cycles.</small>
              </div>

              <div className="setting-group setting-wide">
                <label>Alert Technician Email</label>
                <input
                  type="email"
                  required
                  value={settings.technician_email}
                  onChange={(event) =>
                    setSettings({
                      ...settings,
                      technician_email: event.target.value,
                    })
                  }
                  placeholder="technician@example.com"
                />
                <small>Security alerts will be delivered to this address.</small>
              </div>
            </div>

            {(settingsMessage || settingsError) && (
              <div className={`settings-message ${settingsError ? "error" : "success"}`}>
                {settingsError || settingsMessage}
              </div>
            )}

            <div className="settings-actions">
              <button className="primary-button" type="submit" disabled={settingsSaving}>
                {settingsSaving ? "Saving..." : "Save Settings"}
              </button>
            </div>
          </form>
        </section>

        <footer className="footer">
          <div>
            <strong>NetWatch</strong>
            <span>Enterprise Wi-Fi Monitoring & Analytics</span>
          </div>
          <div>
            {lastUpdated
              ? `Last updated ${lastUpdated.toLocaleTimeString()}`
              : "Waiting for data"}
          </div>
          <div>Open-source • Vendor-independent</div>
        </footer>
      </main>
    </div>
  )
}

export default App
