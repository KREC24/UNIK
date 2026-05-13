import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ConfigProvider, Layout, Menu, theme } from "antd";
import {
  ProjectOutlined,
  UploadOutlined,
  TeamOutlined,
  DashboardOutlined,
} from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ProjectDetail from "./pages/ProjectDetail";
import ClientsPage from "./pages/ClientsPage";

const { Header, Sider, Content } = Layout;

function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "Проекты" },
    { key: "/upload", icon: <UploadOutlined />, label: "Загрузка PDF" },
    { key: "/clients", icon: <TeamOutlined />, label: "Клиенты" },
  ];

  const selectedKey = menuItems.find((item) => location.pathname.startsWith(item.key))?.key || "/";

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider collapsible>
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontWeight: "bold",
            fontSize: 20,
          }}
        >
          UNIK ERP
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Content style={{ padding: 24, background: "#f5f5f5" }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/upload" element={<ProjectDetail />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/clients" element={<ClientsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: { colorPrimary: "#1677ff", borderRadius: 6 },
      }}
    >
      <BrowserRouter>
        <AppLayout />
      </BrowserRouter>
    </ConfigProvider>
  );
}
