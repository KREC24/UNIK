import { useEffect, useState } from "react";
import { Table, Button, Card, Typography, Space, Modal, Input, Form } from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { getClients, createClient } from "../services/api";
import type { Client } from "../types";

const { Title } = Typography;

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    getClients()
      .then(setClients)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (values: Partial<Client>) => {
    const c = await createClient(values);
    setClients((prev) => [...prev, c]);
    setOpen(false);
    form.resetFields();
  };

  const columns = [
    { title: "Название", dataIndex: "name", key: "name" },
    { title: "ИНН", dataIndex: "inn", key: "inn", render: (v: string) => v || "-" },
    {
      title: "Создан",
      dataIndex: "created_at",
      key: "created_at",
      render: (v: string) => new Date(v).toLocaleDateString("ru-RU"),
    },
  ];

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Клиенты
        </Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
          Добавить клиента
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={clients.map((c) => ({ ...c, key: c.id }))}
        loading={loading}
      />
      <Modal
        open={open}
        title="Новый клиент"
        onCancel={() => setOpen(false)}
        onOk={() => form.submit()}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="name" label="Название" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="inn" label="ИНН">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}
