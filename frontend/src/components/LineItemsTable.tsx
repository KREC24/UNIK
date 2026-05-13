import { Table, Tag, Typography } from "antd";
import type { LineItem } from "../types";

const { Text } = Typography;

interface Props {
  items: LineItem[];
}

export default function LineItemsTable({ items }: Props) {
  const columns = [
    {
      title: "Поз",
      dataIndex: "position",
      key: "position",
      width: 60,
    },
    {
      title: "Марка",
      dataIndex: "mark",
      key: "mark",
      width: 100,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: "Наименование",
      dataIndex: "type_name",
      key: "type_name",
      width: 140,
    },
    {
      title: "Кол-во",
      dataIndex: "quantity",
      key: "quantity",
      width: 70,
    },
    {
      title: "Габариты (X×Y×Z)",
      key: "dims",
      width: 180,
      render: (_: unknown, r: LineItem) =>
        r.length_x ? `${r.length_x}×${r.width_y}×${r.height_z} мм` : "-",
    },
    {
      title: "Масса ед.",
      dataIndex: "unit_weight_kg",
      key: "unit_weight_kg",
      width: 90,
      render: (v: number) => (v ? `${v} кг` : "-"),
    },
    {
      title: "Масса общ.",
      dataIndex: "total_weight_kg",
      key: "total_weight_kg",
      width: 100,
      render: (v: number) => (v ? <Text strong>{v} кг</Text> : "-"),
    },
    {
      title: "S ед.",
      dataIndex: "unit_area_m2",
      key: "unit_area_m2",
      width: 80,
      render: (v: number) => (v ? `${v} м²` : "-"),
    },
    {
      title: "S общ.",
      dataIndex: "total_area_m2",
      key: "total_area_m2",
      width: 90,
      render: (v: number) => (v ? <Text strong>{v} м²</Text> : "-"),
    },
  ];

  const totals = items.reduce(
    (acc, item) => ({
      weight: acc.weight + (item.total_weight_kg || 0),
      area: acc.area + (item.total_area_m2 || 0),
      count: acc.count + 1,
    }),
    { weight: 0, area: 0, count: 0 }
  );

  return (
    <div>
      <div style={{ marginBottom: 16, display: "flex", gap: 24 }}>
        <Text>
          Всего позиций: <Text strong>{totals.count}</Text>
        </Text>
        <Text>
          Масса общая: <Text strong>{totals.weight.toFixed(1)} кг</Text>
        </Text>
        <Text>
          Площадь общая: <Text strong>{totals.area.toFixed(2)} м²</Text>
        </Text>
      </div>
      <Table
        columns={columns}
        dataSource={items.map((item, idx) => ({ ...item, key: idx }))}
        size="small"
        scroll={{ x: 1100 }}
        pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (t) => `Всего ${t} строк` }}
      />
    </div>
  );
}
