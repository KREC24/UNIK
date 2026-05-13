import { useEffect, useState } from "react";
import {
  Card,
  Table,
  Button,
  Typography,
  Space,
  Tag,
  Select,
  Modal,
  message,
  theme,
  Descriptions,
} from "antd";
import {
  InboxOutlined,
  MailOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  UserOutlined,
  FilePdfOutlined,
} from "@ant-design/icons";
import {
  getIncomingEmail,
  getIncomingRequests,
  matchIncomingClient,
  processIncomingRequest,
  getClients,
} from "../services/api";
import type { IncomingRequest, Client } from "../types";

const { Title, Text } = Typography;
const { useToken } = theme;

const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
  pending: { color: "default", icon: <ClockCircleOutlined />, label: "Ожидает" },
  matched: { color: "blue", icon: <UserOutlined />, label: "Сопоставлен" },
  processing: { color: "processing", icon: <SyncOutlined spin />, label: "Обработка" },
  processed: { color: "success", icon: <CheckCircleOutlined />, label: "Обработан" },
  failed: { color: "error", icon: <ExclamationCircleOutlined />, label: "Ошибка" },
};

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function IncomingPage() {
  const [requests, setRequests] = useState<IncomingRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [clients, setClients] = useState<Client[]>([]);
  const [matchModal, setMatchModal] = useState<{ open: boolean; requestId: string }>({ open: false, requestId: "" });
  const [selectedClient, setSelectedClient] = useState<string>("");
  const [processing, setProcessing] = useState<string | null>(null);
  const { token } = useToken();

  const loadData = () => {
    setLoading(true);
    getIncomingRequests()
      .then(setRequests)
      .catch(() => message.error("Ошибка загрузки"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    getIncomingEmail().then((r) => setEmail(r.email)).catch(() => {});
    getClients().then(setClients).catch(() => {});
    loadData();
  }, []);

  const handleMatch = async () => {
    if (!selectedClient) return;
    try {
      await matchIncomingClient(matchModal.requestId, selectedClient);
      message.success("Клиент сопоставлен");
      setMatchModal({ open: false, requestId: "" });
      setSelectedClient("");
      loadData();
    } catch {
      message.error("Ошибка сопоставления");
    }
  };

  const handleProcess = async (requestId: string) => {
    setProcessing(requestId);
    try {
      await processIncomingRequest(requestId);
      message.success("Запрос обработан");
      loadData();
    } catch {
      message.error("Ошибка обработки");
    } finally {
      setProcessing(null);
    }
  };

  const columns = [
    {
      title: "Отправитель",
      key: "sender",
      width: 220,
      render: (_: unknown, r: IncomingRequest) => (
        <div>
          <Text strong style={{ fontSize: 13 }}>{r.sender_name || r.sender_email}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>{r.sender_email}</Text>
        </div>
      ),
    },
    {
      title: "Тема",
      dataIndex: "subject",
      key: "subject",
      ellipsis: true,
      render: (v: string) => v || "Без темы",
    },
    {
      title: "Клиент",
      key: "client",
      width: 180,
      render: (_: unknown, r: IncomingRequest) =>
        r.client ? (
          <Tag color="blue">{r.client.name}</Tag>
        ) : (
          <Button
            size="small"
            type="dashed"
            icon={<UserOutlined />}
            onClick={() => { setMatchModal({ open: true, requestId: r.id }); setSelectedClient(""); }}
          >
            Сопоставить
          </Button>
        ),
    },
    {
      title: "Вложения",
      dataIndex: "attachments",
      key: "attachments",
      width: 100,
      render: (v: string[]) => (
        <Space>
          <FilePdfOutlined style={{ color: token.colorError }} />
          <Text>{v?.length ?? 0}</Text>
        </Space>
      ),
    },
    {
      title: "Статус",
      dataIndex: "status",
      key: "status",
      width: 130,
      render: (v: string) => {
        const cfg = statusConfig[v] || statusConfig.pending;
        return <Tag color={cfg.color} icon={cfg.icon}>{cfg.label}</Tag>;
      },
    },
    {
      title: "Дата",
      dataIndex: "received_at",
      key: "received_at",
      width: 120,
      render: (v: string) => <Text type="secondary" style={{ fontSize: 12 }}>{formatDate(v)}</Text>,
    },
    {
      title: "",
      key: "actions",
      width: 100,
      render: (_: unknown, r: IncomingRequest) => (
        <Button
          type="primary"
          size="small"
          icon={<ThunderboltOutlined />}
          loading={processing === r.id}
          disabled={r.status === "processed" || r.status === "processing"}
          onClick={() => handleProcess(r.id)}
        >
          В работу
        </Button>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <Title level={2} style={{ margin: 0, fontWeight: 700 }}>
            <InboxOutlined style={{ marginRight: 10, color: token.colorPrimary }} />
            Входящие
          </Title>
          <Text type="secondary" style={{ fontSize: 14 }}>
            Обработка входящих запросов от клиентов
          </Text>
        </div>
      </div>

      <Card
        style={{
          marginBottom: 24,
          borderRadius: token.borderRadiusLG,
          background: token.colorBgContainer,
          border: `1px solid ${token.colorBorderSecondary}`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <MailOutlined style={{ fontSize: 28, color: token.colorPrimary }} />
          <div style={{ flex: 1 }}>
            <Text type="secondary" style={{ fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Адрес для приёма запросов
            </Text>
            <br />
            <Text copyable style={{ fontSize: 20, fontWeight: 600, fontFamily: "monospace" }}>
              {email}
            </Text>
          </div>
          <Text type="secondary" style={{ fontSize: 12, maxWidth: 220, textAlign: "right" }}>
            Клиенты отправляют письма с чертежами на этот адрес. Система автоматически определит отправителя.
          </Text>
        </div>
      </Card>

      <Card styles={{ body: { padding: "16px 24px" } }} style={{ borderRadius: token.borderRadiusLG }}>
        <Table
          columns={columns}
          dataSource={requests.map((r) => ({ ...r, key: r.id }))}
          loading={loading}
          size="middle"
          pagination={{ pageSize: 15 }}
          locale={{ emptyText: "Нет входящих запросов" }}
        />
      </Card>

      <Modal
        title="Сопоставить с клиентом"
        open={matchModal.open}
        onOk={handleMatch}
        onCancel={() => setMatchModal({ open: false, requestId: "" })}
        okText="Сопоставить"
        cancelText="Отмена"
      >
        <Select
          showSearch
          placeholder="Выберите клиента из базы"
          optionFilterProp="label"
          value={selectedClient || undefined}
          onChange={(v) => setSelectedClient(v)}
          style={{ width: "100%" }}
          options={clients.map((c) => ({ label: c.name, value: c.id }))}
        />
      </Modal>
    </div>
  );
}
