import { useState, useEffect } from "react";
import { Button, Modal, Select, Input, DatePicker, Form, message, Tooltip } from "antd";
import { SendOutlined } from "@ant-design/icons";
import { getEmployees, assignTask } from "../services/api";
import type { Employee } from "../types";
import dayjs from "dayjs";

interface Props {
  mark: string;
  quantity?: number;
  totalWeightKg?: number;
  projectId?: string;
  lineItemId?: string;
  drawingUrl?: string;
  size?: "small" | "middle" | "large";
}

export default function SendTaskButton({ mark, quantity = 1, totalWeightKg = 0, projectId, lineItemId, drawingUrl, size = "small" }: Props) {
  const [open, setOpen] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selectedEmp, setSelectedEmp] = useState<string>("");
  const [notes, setNotes] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    if (open) getEmployees().then(setEmployees).catch(() => {});
  }, [open]);

  const handleSend = async () => {
    if (!selectedEmp) return;
    setSending(true);
    try {
      await assignTask({
        mark,
        assigned_to: selectedEmp,
        quantity,
        total_weight_kg: totalWeightKg,
        project_id: projectId || "",
        line_item_id: lineItemId || "",
        drawing_url: drawingUrl || "",
        notes,
      });
      message.success(`Задача по марке ${mark} отправлена`);
      setOpen(false);
      setSelectedEmp("");
      setNotes("");
    } catch (e: unknown) {
      message.error("Ошибка: " + ((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || ""));
    }
    setSending(false);
  };

  return (
    <>
      <Tooltip title="Отправить задачу">
        <Button
          type="text"
          size={size}
          icon={<SendOutlined style={{ color: "#1677ff" }} />}
          onClick={() => setOpen(true)}
        />
      </Tooltip>
      <Modal
        title={`Новая задача: ${mark}`}
        open={open}
        onOk={handleSend}
        onCancel={() => setOpen(false)}
        okText="Отправить"
        cancelText="Отмена"
        confirmLoading={sending}
      >
        <div style={{ marginBottom: 12 }}>
          <div>Марка: <b>{mark}</b></div>
          <div>Кол-во: <b>{quantity}</b></div>
          <div>Вес: <b>{totalWeightKg} кг</b></div>
        </div>
        <Select
          showSearch
          placeholder="Выберите сотрудника"
          optionFilterProp="label"
          value={selectedEmp || undefined}
          onChange={(v) => setSelectedEmp(v)}
          style={{ width: "100%", marginBottom: 12 }}
          options={employees.map((e) => ({ label: e.full_name, value: e.id }))}
        />
        <Input.TextArea
          placeholder="Примечание (опционально)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
        />
      </Modal>
    </>
  );
}
