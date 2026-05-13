import { useEffect, useState } from "react";
import {
  Card,
  Row,
  Col,
  Table,
  Button,
  Typography,
  Space,
  Tag,
  Skeleton,
  Tooltip,
  theme,
} from "antd";
import {
  ProjectOutlined,
  GoldOutlined,
  FileOutlined,
  BarChartOutlined,
  AppstoreOutlined,
  FilePdfOutlined,
  EyeOutlined,
  UploadOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getDashboard } from "../services/api";
import type { DashboardStats, RecentFile } from "../types";

const { Title, Text } = Typography;
const { useToken } = theme;

function formatWeight(kg: number): string {
  if (kg >= 1_000_000) return `${(kg / 1_000_000).toFixed(2)} тыс. т`;
  if (kg >= 1_000) return `${(kg / 1_000).toFixed(1)} т`;
  return `${kg.toFixed(1)} кг`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function batchTypeTag(t: string) {
  const map: Record<string, { color: string; label: string }> = {
    kmd: { color: "blue", label: "КМД" },
    general: { color: "green", label: "Общие данные" },
    shipping: { color: "geekblue", label: "Ведомость" },
  };
  const m = map[t] || { color: "default", label: t };
  return <Tag color={m.color}>{m.label}</Tag>;
}

const statCardBodyStyle = (token: ReturnType<typeof useToken>["token"], isDark: boolean): React.CSSProperties => ({
  background: isDark
    ? "linear-gradient(135deg, #13203a 0%, #1a2d4a 50%, #0d2948 100%)"
    : "linear-gradient(135deg, #e8edf5 0%, #dfe7f5 50%, #d0ddf0 100%)",
  border: isDark
    ? `1px solid ${token.colorBorderSecondary}`
    : `1px solid ${token.colorBorderBg}`,
  borderRadius: token.borderRadiusLG,
  padding: "20px 24px",
  transition: "all 0.3s ease",
  minHeight: 124,
  display: "flex",
  flexDirection: "column",
  justifyContent: "center",
});

const statCardOuterStyle: React.CSSProperties = {
  padding: 0,
  overflow: "hidden",
  borderRadius: 0,
};

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { token } = useToken();
  const isDark = token.colorBgLayout === "#000000"
    || token.colorBgContainer === "#1f1f1f"
    || token.colorBgBase === "#000000";

  const statTextColor = isDark ? "rgba(255,255,255,0.85)" : "rgba(0,0,0,0.88)";
  const statSecondaryColor = isDark ? "rgba(255,255,255,0.55)" : "rgba(0,0,0,0.45)";

  useEffect(() => {
    getDashboard()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const recentColumns = [
    {
      title: "Файл",
      dataIndex: "source_file",
      key: "source_file",
      ellipsis: true,
      render: (v: string) => (
        <Space>
          <FilePdfOutlined style={{ color: token.colorPrimary }} />
          <Text ellipsis style={{ maxWidth: 320 }}>{v}</Text>
        </Space>
      ),
    },
    {
      title: "Тип",
      dataIndex: "batch_type",
      key: "batch_type",
      width: 120,
      render: (v: string) => batchTypeTag(v),
    },
    {
      title: "Строк",
      dataIndex: "total_items",
      key: "total_items",
      width: 80,
      align: "right" as const,
      render: (v: number) => (
        <Text strong>{v}</Text>
      ),
    },
    {
      title: "Дата",
      dataIndex: "created_at",
      key: "created_at",
      width: 160,
      render: (v: string) => (
        <Text type="secondary" style={{ fontSize: 13 }}>
          {formatDate(v)}
        </Text>
      ),
    },
    {
      title: "",
      key: "actions",
      width: 100,
      render: (_: unknown, record: RecentFile) => (
        <Tooltip title="Открыть результаты парсинга">
          <Button
            type="primary"
            size="small"
            ghost
            icon={<EyeOutlined />}
            onClick={() => navigate(`/upload?batch=${record.batch_id}`)}
          >
            Смотреть
          </Button>
        </Tooltip>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 28,
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0, fontWeight: 700, letterSpacing: "-0.02em" }}>
            Дашборд
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            Обзор проектов и загруженных данных
          </Text>
        </div>
        <Button
          type="primary"
          size="large"
          icon={<UploadOutlined />}
          onClick={() => navigate("/upload")}
        >
          Загрузить PDF
        </Button>
      </div>

      {loading ? (
        <Row gutter={[20, 20]}>
          {[1, 2, 3, 4].map((i) => (
            <Col xs={24} sm={12} lg={6} key={i}>
              <Card>
                <Skeleton active paragraph={{ rows: 1 }} />
              </Card>
            </Col>
          ))}
        </Row>
      ) : (
        <Row gutter={[20, 20]}>
          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              style={statCardOuterStyle}
              styles={{ body: statCardBodyStyle(token, isDark) }}
              onClick={() => navigate("/projects")}
            >
              <div style={{ marginBottom: 4 }}>
                <Space>
                  <ProjectOutlined style={{ color: token.colorPrimary, fontSize: 16 }} />
                  <Text style={{ color: statSecondaryColor, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 500 }}>
                    Проекты
                  </Text>
                </Space>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                <Text style={{ color: statTextColor, fontSize: 34, fontWeight: 700, lineHeight: 1 }}>
                  {stats?.total_projects ?? 0}
                </Text>
                <Text style={{ color: statSecondaryColor, fontSize: 14 }}>шт.</Text>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              style={statCardOuterStyle}
              styles={{ body: statCardBodyStyle(token, isDark) }}
            >
              <div style={{ marginBottom: 4 }}>
                <Space>
                  <GoldOutlined style={{ color: token.colorWarning, fontSize: 16 }} />
                  <Text style={{ color: statSecondaryColor, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 500 }}>
                    Тоннаж
                  </Text>
                </Space>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                <Text style={{ color: statTextColor, fontSize: 34, fontWeight: 700, lineHeight: 1 }}>
                  {stats ? formatWeight(stats.total_weight_kg) : "0"}
                </Text>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              style={statCardOuterStyle}
              styles={{ body: statCardBodyStyle(token, isDark) }}
            >
              <div style={{ marginBottom: 4 }}>
                <Space>
                  <AppstoreOutlined style={{ color: token.colorSuccess, fontSize: 16 }} />
                  <Text style={{ color: statSecondaryColor, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 500 }}>
                    Элементы
                  </Text>
                </Space>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                <Text style={{ color: statTextColor, fontSize: 34, fontWeight: 700, lineHeight: 1 }}>
                  {stats?.total_items ?? 0}
                </Text>
                <Text style={{ color: statSecondaryColor, fontSize: 14 }}>поз.</Text>
              </div>
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card
              hoverable
              style={statCardOuterStyle}
              styles={{ body: statCardBodyStyle(token, isDark) }}
            >
              <div style={{ marginBottom: 4 }}>
                <Space>
                  <BarChartOutlined style={{ color: token.colorInfo, fontSize: 16 }} />
                  <Text style={{ color: statSecondaryColor, fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 500 }}>
                    Файлы
                  </Text>
                </Space>
              </div>
              <div style={{ display: "flex", alignItems: "baseline", gap: 4 }}>
                <Text style={{ color: statTextColor, fontSize: 34, fontWeight: 700, lineHeight: 1 }}>
                  {stats?.recent_files?.length ?? 0}
                </Text>
                <Text style={{ color: statSecondaryColor, fontSize: 14 }}>загруж.</Text>
              </div>
            </Card>
          </Col>
        </Row>
      )}

      <Card
        style={{ marginTop: 28, borderRadius: token.borderRadiusLG }}
        styles={{ body: { padding: "20px 24px" } }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <Space>
            <FileOutlined style={{ fontSize: 18, color: token.colorPrimary }} />
            <Title level={4} style={{ margin: 0, fontWeight: 600 }}>
              Последние загрузки
            </Title>
          </Space>
          <Button type="link" icon={<UploadOutlined />} onClick={() => navigate("/upload")}>
            Загрузить ещё
          </Button>
        </div>

        <Table
          columns={recentColumns}
          dataSource={(stats?.recent_files ?? []).map((f) => ({ ...f, key: f.batch_id }))}
          loading={loading}
          size="middle"
          pagination={false}
          locale={{ emptyText: "Нет загруженных файлов" }}
          style={{ marginTop: 4 }}
        />
      </Card>
    </div>
  );
}
