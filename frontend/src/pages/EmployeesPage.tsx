import { useEffect, useState } from "react";
import {
  Card, Table, Button, Typography, Space, Tag, Modal, Input, Select, Switch, Form, Popconfirm, message, theme,
} from "antd";
import { PlusOutlined, SendOutlined } from "@ant-design/icons";
import { getEmployees, createEmployee, updateEmployee, deleteEmployee } from "../services/api";
import type { Employee } from "../types";

const { Title } = Typography;
const ROLE_OPTIONS = [
  { label: "Гл. инженер", value: "chief_engineer" },
  { label: "Нач. участка", value: "shop_master" },
  { label: "Рабочий", value: "worker" },
  { label: "Менеджер", value: "manager" },
  { label: "Снабжение", value: "supply" },
];
const ROLE_LABELS: Record<string, string> = Object.fromEntries(ROLE_OPTIONS.map((r) => [r.value, r.label]));

export default function EmployeesPage() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [form] = Form.useForm();
  const { token } = theme.useToken();
  const [sending, setSending] = useState(false);

  const load = () => {
    setLoading(true);
    getEmployees().then(setEmployees).catch(() => {}).finally(() => setLoading(false));
  };
  useEffect(load, []);

  const openCreate = () => { setEditing(null); form.resetFields(); setModalOpen(true); };
  const openEdit = (e: Employee) => { setEditing(e); form.setFieldsValue(e); setModalOpen(true); };

  const handleSave = async () => {
    const vals = await form.validateFields();
    if (editing) {
      await updateEmployee(editing.id, vals);
      message.success("Обновлено");
    } else {
      await createEmployee(vals);
      message.success("Создан");
    }
    setModalOpen(false);
    load();
  };

  const handleDelete = async (id: string) => {
    await deleteEmployee(id);
    message.success("Удалён");
    load();
  };

  const columns = [
    { title: "ФИО", dataIndex: "full_name", key: "full_name" },
    {
      title: "Роль", dataIndex: "role", key: "role", width: 150,
      render: (v: string) => <Tag>{ROLE_LABELS[v] || v}</Tag>,
    },
    { title: "Отдел", dataIndex: "department", key: "department", width: 150, render: (v: string) => v || "-" },
    {
      title: "Telegram ID", dataIndex: "telegram_id", key: "telegram_id", width: 150,
      render: (v: string) => v ? <Tag color="blue">{v}</Tag> : <Tag color="default">не указан</Tag>,
    },
    {
      title: "Активен", dataIndex: "is_active", key: "is_active", width: 80,
      render: (v: boolean) => v ? <Tag color="success">Да</Tag> : <Tag color="error">Нет</Tag>,
    },
    {
      title: "", key: "actions", width: 120,
      render: (_: unknown, r: Employee) => (
        <Space>
          <Button size="small" onClick={() => openEdit(r)}>Ред.</Button>
          <Popconfirm title="Удалить?" onConfirm={() => handleDelete(r.id)}>
            <Button size="small" danger>Уд.</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <Title level={2} style={{ margin: 0 }}>Сотрудники</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>Добавить</Button>
      </div>

      <Card styles={{ body: { padding: "16px 24px" } }}>
        <Table
          columns={columns}
          dataSource={employees.map((e) => ({ ...e, key: e.id }))}
          loading={loading}
          size="middle"
        />
      </Card>

      <Modal
        title={editing ? "Редактировать сотрудника" : "Новый сотрудник"}
        open={modalOpen}
        onOk={handleSave}
        onCancel={() => setModalOpen(false)}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical">
          <Form.Item name="full_name" label="ФИО" rules={[{ required: true }]}>
            <Input placeholder="Иванов Иван" />
          </Form.Item>
          <Form.Item name="role" label="Роль" initialValue="worker">
            <Select options={ROLE_OPTIONS} />
          </Form.Item>
          <Form.Item name="department" label="Отдел">
            <Input placeholder="Цех №1" />
          </Form.Item>
          <Form.Item name="telegram_id" label="Telegram ID">
            <Input placeholder="123456789" />
          </Form.Item>
          <Form.Item name="is_active" label="Активен" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
