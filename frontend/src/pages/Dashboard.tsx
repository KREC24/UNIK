import { useEffect, useState } from "react";
import { Table, Button, Card, Typography, Space, Tag } from "antd";
import { PlusOutlined, UploadOutlined, ExportOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import { getProjects } from "../services/api";
import type { Project } from "../types";

const { Title } = Typography;

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    getProjects()
      .then(setProjects)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    {
      title: "Шифр проекта",
      dataIndex: "external_code",
      key: "external_code",
      render: (v: string) => v || "-",
    },
    {
      title: "Название",
      dataIndex: "name",
      key: "name",
      render: (v: string) => v || "Без названия",
    },
    {
      title: "Стадия",
      dataIndex: "stage",
      key: "stage",
      render: (v: string) => (v ? <Tag>{v}</Tag> : "-"),
    },
    {
      title: "",
      key: "actions",
      width: 120,
      render: (_: unknown, record: Project) => (
        <Button type="link" onClick={() => navigate(`/projects/${record.id}`)}>
          Открыть
        </Button>
      ),
    },
  ];

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Проекты
        </Title>
        <Space>
          <Button icon={<UploadOutlined />} onClick={() => navigate("/upload")}>
            Загрузить PDF
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate("/projects/new")}>
            Новый проект
          </Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={projects.map((p) => ({ ...p, key: p.id }))}
        loading={loading}
        size="middle"
      />
    </Card>
  );
}
