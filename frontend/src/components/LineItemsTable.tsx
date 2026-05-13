import { useMemo } from "react";
import { Table, Tag, Typography } from "antd";
import type { LineItem, OgzPositionResult, OgzCalculationTotals } from "../types";

const { Text } = Typography;

interface Props {
  items: LineItem[];
  ogzResults?: OgzPositionResult[];
  ogzTotals?: OgzCalculationTotals;
  ogzKraskaName?: string;
}

export default function LineItemsTable({ items, ogzResults, ogzTotals, ogzKraskaName }: Props) {
  const showOgz = !!(ogzResults && ogzResults.length > 0);

  const ogzByMark = useMemo(() => {
    if (!ogzResults) return new Map<string, OgzPositionResult>();
    const map = new Map<string, OgzPositionResult>();
    ogzResults.forEach((r, i) => {
      map.set(r.mark || `_idx_${i}`, r);
    });
    return map;
  }, [ogzResults]);

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
      width: 110,
      render: (v: string) => <Tag color="blue">{v}</Tag>,
    },
    {
      title: "Наименование",
      dataIndex: "type_name",
      key: "type_name",
      ellipsis: true,
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
      ellipsis: true,
      render: (_: unknown, r: LineItem) =>
        r.length_x ? `${r.length_x}×${r.width_y}×${r.height_z} мм` : "-",
    },
    {
      title: "Масса ед.",
      dataIndex: "unit_weight_kg",
      key: "unit_weight_kg",
      width: 95,
      render: (v: number) => (v != null ? `${v.toFixed(1)} кг` : "-"),
    },
    {
      title: "Масса общ.",
      dataIndex: "total_weight_kg",
      key: "total_weight_kg",
      width: 105,
      render: (v: number) => (v != null ? <Text strong>{v.toFixed(1)} кг</Text> : "-"),
    },
    {
      title: "S ед.",
      dataIndex: "unit_area_m2",
      key: "unit_area_m2",
      width: 80,
      render: (v: number) => (v != null ? `${v.toFixed(2)} м²` : "-"),
    },
    {
      title: "S общ.",
      dataIndex: "total_area_m2",
      key: "total_area_m2",
      width: 90,
      render: (v: number) => (v != null ? <Text strong>{v.toFixed(2)} м²</Text> : "-"),
    },
    {
      title: "PTM",
      dataIndex: "ptm",
      key: "ptm",
      width: 70,
      render: (v: number) => (v != null ? `${v.toFixed(1)} мм` : "-"),
    },
    ...(showOgz
      ? [
          {
            title: ogzKraskaName || "ОГЗ-состав",
            key: "ogz_composition",
            ellipsis: true,
            render: (_: unknown, r: LineItem, idx: number) => {
              const ogz = ogzByMark.get(r.mark || `_idx_${idx}`);
              if (!ogz) return "-";
              return (
                <Text style={{ fontSize: 12 }}>
                  {ogz.matched_composition_name || "не подобран"}
                </Text>
              );
            },
          },
          {
            title: "Грунт, кг",
            key: "ogz_grunt",
            width: 90,
            render: (_: unknown, r: LineItem, idx: number) => {
              const ogz = ogzByMark.get(r.mark || `_idx_${idx}`);
              return ogz ? ogz.grunt_consumption_kg.toFixed(1) : "-";
            },
          },
          {
            title: "Краска, кг",
            key: "ogz_kraska",
            width: 100,
            render: (_: unknown, r: LineItem, idx: number) => {
              const ogz = ogzByMark.get(r.mark || `_idx_${idx}`);
              return ogz ? <Text strong>{ogz.kraska_consumption_kg.toFixed(1)}</Text> : "-";
            },
          },
          {
            title: "Финиш, кг",
            key: "ogz_finish",
            width: 90,
            render: (_: unknown, r: LineItem, idx: number) => {
              const ogz = ogzByMark.get(r.mark || `_idx_${idx}`);
              return ogz ? ogz.finish_consumption_kg.toFixed(1) : "-";
            },
          },
          {
            title: "Стоимость, ₽",
            key: "ogz_cost",
            width: 110,
            render: (_: unknown, r: LineItem, idx: number) => {
              const ogz = ogzByMark.get(r.mark || `_idx_${idx}`);
              return ogz ? <Text strong>{ogz.position_cost_rub.toFixed(0)}</Text> : "-";
            },
          },
        ]
      : []),
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
    <div style={{ width: "100%" }}>
      <div style={{ marginBottom: 16, display: "flex", gap: 24, flexWrap: "wrap" }}>
        <Text>
          Всего позиций: <Text strong>{totals.count}</Text>
        </Text>
        <Text>
          Масса общая: <Text strong>{totals.weight.toFixed(1)} кг</Text>
        </Text>
        <Text>
          Площадь общая: <Text strong>{totals.area.toFixed(2)} м²</Text>
        </Text>
        {ogzTotals && (
          <>
            <Text>
              Грунт: <Text strong>{ogzTotals.grunt_consumption_kg.toFixed(1)} кг</Text>
            </Text>
            <Text>
              Краска: <Text strong>{ogzTotals.kraska_consumption_kg.toFixed(1)} кг</Text>
            </Text>
            <Text>
              Финиш: <Text strong>{ogzTotals.finish_consumption_kg.toFixed(1)} кг</Text>
            </Text>
            <Text>
              Стоимость:{" "}
              <Text strong>
                {ogzTotals.total_material_cost_rub.toLocaleString("ru-RU")} ₽
              </Text>
            </Text>
          </>
        )}
      </div>
      <Table
        columns={columns}
        dataSource={items.map((item, idx) => ({ ...item, key: idx }))}
        size="small"
        tableLayout="auto"
        pagination={{ pageSize: 50, showSizeChanger: true, showTotal: (t) => `Всего ${t} строк` }}
      />
    </div>
  );
}
