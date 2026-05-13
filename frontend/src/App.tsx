import { useState, useCallback, useEffect, useSyncExternalStore, useRef } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import {
  ConfigProvider,
  Layout,
  Menu,
  Switch,
  Input,
  Typography,
  theme,
} from "antd";
import {
  SearchOutlined,
  ClockCircleOutlined,
  InboxOutlined,
  TeamOutlined,
  DashboardOutlined,
  SettingOutlined,
  SunOutlined,
  MoonOutlined,
  ProjectOutlined,
  FilePdfOutlined,
  IdcardOutlined,
  SyncOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ProjectsPage from "./pages/ProjectsPage";
import IncomingPage from "./pages/IncomingPage";
import ProjectDetail from "./pages/ProjectDetail";
import ClientsPage from "./pages/ClientsPage";
import EmployeesPage from "./pages/EmployeesPage";
import SettingsPage from "./pages/SettingsPage";
import { getAppName, subscribeAppName, setAppName, getCompanyName, subscribeCompanyName, setCompanyName } from "./services/state";
import { getSettings, searchAll, getTaskStats } from "./services/api";
import type { SearchResults, TaskStats } from "./types";

const { Sider, Content } = Layout;
const { Text } = Typography;

function getInitialTheme(): boolean {
  const stored = localStorage.getItem("unik-theme");
  if (stored === "dark") return true;
  if (stored === "light") return false;
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export default function App() {
  const [isDark, setIsDark] = useState(getInitialTheme);

  const toggleTheme = useCallback(() => {
    setIsDark((prev) => {
      const next = !prev;
      localStorage.setItem("unik-theme", next ? "dark" : "light");
      return next;
    });
  }, []);

  return (
    <ConfigProvider
      theme={{
        algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: { colorPrimary: "#1677ff", borderRadius: 6 },
      }}
    >
      <BrowserRouter>
        <AppLayout isDark={isDark} onToggleTheme={toggleTheme} />
      </BrowserRouter>
    </ConfigProvider>
  );
}

function AppLayout({
  isDark,
  onToggleTheme,
}: {
  isDark: boolean;
  onToggleTheme: () => void;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const searchRef = useRef<HTMLDivElement>(null);

  const appName = useSyncExternalStore(subscribeAppName, getAppName, getAppName);
  const companyName = useSyncExternalStore(subscribeCompanyName, getCompanyName, getCompanyName);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchTimer, setSearchTimer] = useState<ReturnType<typeof setTimeout> | null>(null);
  const [clockTime, setClockTime] = useState(new Date());
  const [taskStats, setTaskStats] = useState<TaskStats>({ active: 0, pending: 0 });
  const { token } = theme.useToken();

  const isDarkToken = token.colorBgLayout === "#000000"
    || token.colorBgContainer === "#1f1f1f"
    || token.colorBgBase === "#000000";

  useEffect(() => {
    document.title = appName;
    getSettings()
      .then((res) => {
        const admin = res.settings?.admin;
        if (admin?.app_name) setAppName(admin.app_name);
        if (admin?.company_name !== undefined) setCompanyName(admin.company_name);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setClockTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    getTaskStats().then(setTaskStats).catch(() => {});
    const timer = setInterval(() => getTaskStats().then(setTaskStats).catch(() => {}), 15000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setSearchOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleSearch = useCallback((value: string) => {
    setSearchQuery(value);
    if (searchTimer) clearTimeout(searchTimer);
    if (value.trim().length < 2) {
      setSearchResults(null);
      setSearchOpen(false);
      return;
    }
    const timer = setTimeout(() => {
      searchAll(value.trim())
        .then((res) => {
          setSearchResults(res);
          setSearchOpen(res.total > 0);
        })
        .catch(() => setSearchResults(null));
    }, 300);
    setSearchTimer(timer);
  }, [searchTimer]);

  const closeSearch = () => { setSearchOpen(false); setSearchQuery(""); };

  const clockStr = clockTime.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const dateStr = clockTime.toLocaleDateString("ru-RU", { day: "2-digit", month: "long", weekday: "short" });
  const tzStr = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const textColor = isDarkToken ? "rgba(255,255,255,0.85)" : "rgba(0,0,0,0.88)";
  const headerBg = isDarkToken ? "#1f1f1f" : "#fff";
  const headerBorder = isDarkToken ? "#303030" : "#f0f0f0";

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "Дашборд" },
    { key: "/projects", icon: <ProjectOutlined />, label: "Проекты" },
    { key: "/incoming", icon: <InboxOutlined />, label: "Входящие" },
    { key: "/clients", icon: <TeamOutlined />, label: "Клиенты" },
    { key: "/employees", icon: <IdcardOutlined />, label: "Сотрудники" },
    { key: "/settings", icon: <SettingOutlined />, label: "Настройки" },
  ];

  const selectedKey =
    menuItems.find((item) => item.key !== "/" && location.pathname.startsWith(item.key))?.key || "/";

  const headerTransition = "all 0.3s ease";

  return (
    <>
      <Layout style={{ minHeight: "100vh" }}>
        <Sider collapsible>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            height: "calc(100% - 48px)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: 64,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontWeight: "bold",
              fontSize: 18,
              userSelect: "none",
              padding: "0 8px",
              textAlign: "center",
              lineHeight: 1.3,
              flexShrink: 0,
            }}
          >
            {appName}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[selectedKey]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ flex: 1, overflow: "auto" }}
          />
          <div
            style={{
              padding: "12px 16px 8px",
              borderTop: `1px solid ${isDarkToken ? "#303030" : "#f0f0f0"}`,
              color: "rgba(255,255,255,0.55)",
              fontSize: 12,
              textAlign: "center",
              userSelect: "none",
              flexShrink: 0,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {companyName}
          </div>
        </div>
      </Sider>
      <Layout>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
            padding: "8px 24px",
            background: headerBg,
            borderBottom: `1px solid ${headerBorder}`,
            transition: headerTransition,
            minHeight: 52,
          }}
        >
          <div
            ref={searchRef}
            style={{
              flex: "1 1 280px",
              maxWidth: 600,
              minWidth: 200,
              position: "relative",
              transition: headerTransition,
            }}
          >
            <Input
              size="middle"
              placeholder="Поиск по проектам, клиентам, документам..."
              prefix={<SearchOutlined style={{ color: token.colorTextQuaternary }} />}
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => { if (searchResults && searchResults.total > 0) setSearchOpen(true); }}
              allowClear
              style={{
                borderRadius: 20,
                transition: headerTransition,
                boxShadow: searchQuery ? `0 0 0 2px ${token.colorPrimary}33` : undefined,
              }}
            />
            {searchOpen && searchResults && (
                <div
                  style={{
                    position: "absolute",
                    top: "100%",
                    left: 0,
                    right: 0,
                    zIndex: 1050,
                    marginTop: 4,
                    background: token.colorBgContainer,
                    borderRadius: token.borderRadiusLG,
                    boxShadow: token.boxShadowSecondary,
                    border: `1px solid ${token.colorBorderSecondary}`,
                    overflow: "hidden",
                  }}
                >
                  {searchResults.projects.length > 0 && (
                    <div style={{ padding: "6px 16px 2px" }}>
                      <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>Проекты</Text>
                    </div>
                  )}
                  {searchResults.projects.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => { navigate(`/projects/${p.id}`); closeSearch(); }}
                      style={{ padding: "6px 16px", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = token.colorBgTextHover; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
                    >
                      <ProjectOutlined style={{ color: token.colorPrimary }} />
                      <Text strong style={{ flex: 1, fontSize: 13 }}>{p.name || p.external_code || "Без названия"}</Text>
                    </div>
                  ))}
                  {searchResults.clients.length > 0 && (
                    <div style={{ padding: "6px 16px 2px", borderTop: searchResults.projects.length > 0 ? `1px solid ${token.colorBorderSecondary}` : "none" }}>
                      <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>Клиенты</Text>
                    </div>
                  )}
                  {searchResults.clients.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => { navigate("/clients"); closeSearch(); }}
                      style={{ padding: "6px 16px", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = token.colorBgTextHover; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
                    >
                      <TeamOutlined style={{ color: token.colorSuccess }} />
                      <Text strong style={{ flex: 1, fontSize: 13 }}>{c.name}</Text>
                      {c.inn && <Text type="secondary" style={{ fontSize: 11 }}>ИНН {c.inn}</Text>}
                    </div>
                  ))}
                  {searchResults.batches.length > 0 && (
                    <div style={{ padding: "6px 16px 2px", borderTop: (searchResults.projects.length + searchResults.clients.length) > 0 ? `1px solid ${token.colorBorderSecondary}` : "none" }}>
                      <Text type="secondary" style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>Документы</Text>
                    </div>
                  )}
                  {searchResults.batches.map((b) => (
                    <div
                      key={b.batch_id}
                      onClick={() => { navigate(`/upload?batch=${b.batch_id}`); closeSearch(); }}
                      style={{ padding: "6px 16px", cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}
                      onMouseEnter={(e) => { (e.currentTarget as HTMLDivElement).style.background = token.colorBgTextHover; }}
                      onMouseLeave={(e) => { (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
                    >
                      <FilePdfOutlined style={{ color: token.colorError }} />
                      <Text strong style={{ flex: 1, fontSize: 13 }} ellipsis>{b.source_file}</Text>
                    </div>
                  ))}
                </div>
              )}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0, flexWrap: "wrap", transition: headerTransition }}>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "6px 14px",
                borderRadius: 20,
                background: isDarkToken ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)",
                border: `1px solid ${token.colorBorderSecondary}`,
                whiteSpace: "nowrap",
                flexShrink: 0,
                transition: headerTransition,
              }}
            >
              <ClockCircleOutlined style={{ fontSize: 16, color: token.colorPrimary }} />
              <div>
                <Text
                  style={{
                    color: textColor,
                    fontSize: 16,
                    fontWeight: 600,
                    fontFamily: "'JetBrains Mono', 'Courier New', 'Consolas', monospace",
                    fontVariantNumeric: "tabular-nums",
                    display: "block",
                    lineHeight: 1.2,
                    letterSpacing: "0.02em",
                  }}
                >
                  {clockStr}
                </Text>
                <Text type="secondary" style={{ fontSize: 10, display: "block", lineHeight: 1.3 }}>
                  {dateStr} · {tzStr}
                </Text>
              </div>
            </div>

            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: token.colorPrimary,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontWeight: 600,
                fontSize: 14,
                cursor: "default",
                userSelect: "none",
                flexShrink: 0,
              }}
              title="Профиль пользователя"
            >
              А
            </div>
            <SunOutlined style={{ fontSize: 14, color: isDarkToken ? "rgba(255,255,255,0.45)" : "#faad14", flexShrink: 0 }} />
            <Switch size="small" checked={isDark} onChange={onToggleTheme} style={{ flexShrink: 0 }} />
            <MoonOutlined style={{ fontSize: 14, color: isDarkToken ? "#faad14" : "rgba(0,0,0,0.45)", flexShrink: 0 }} />
          </div>
        </div>
        <Content style={{ padding: 24, paddingBottom: 54, background: isDarkToken ? "#141414" : "#f5f5f5" }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/incoming" element={<IncomingPage />} />
            <Route path="/upload" element={<ProjectDetail />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/clients" element={<ClientsPage />} />
            <Route path="/employees" element={<EmployeesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
    <footer
        className="app-footer"
        style={{
          background: isDarkToken
            ? "rgba(20,20,20,0.85)"
            : "rgba(255,255,255,0.85)",
          borderTopColor: isDarkToken ? "#303030" : "#ddd",
          color: isDarkToken ? "rgba(255,255,255,0.55)" : "rgba(0,0,0,0.55)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 24, justifyContent: "center", flexWrap: "wrap" }}>
          <span>{companyName}</span>
          <span style={{ opacity: 0.3 }}>|</span>
          <span>
            <SyncOutlined spin style={{ marginRight: 4, color: token.colorWarning }} />
            В работе: <b>{taskStats.active}</b> марок
          </span>
          <span style={{ opacity: 0.3 }}>|</span>
          <span>
            <ClockCircleOutlined style={{ marginRight: 4, color: token.colorTextQuaternary }} />
            Ожидает: <b>{taskStats.pending}</b>
          </span>
        </div>
      </footer>
    </>
  );
}
