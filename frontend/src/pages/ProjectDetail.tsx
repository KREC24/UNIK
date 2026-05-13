import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Card,
  Typography,
  Descriptions,
  Tag,
  Button,
  Space,
  Spin,
  Tabs,
  Select,
  message,
} from "antd";
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  CalculatorOutlined,
} from "@ant-design/icons";
import { getProjectDetails, getExportUrl, calculateOgz } from "../services/api";
import PdfUploader from "../components/PdfUploader";
import LineItemsTable from "../components/LineItemsTable";
import type { ParseResult, Project, OgzCalculationResponse } from "../types";

const { Title, Text } = Typography;

const REI_OPTIONS = [
  { value: 45, label: "R45" },
  { value: 60, label: "R60" },
  { value: 90, label: "R90" },
  { value: 120, label: "R120" },
  { value: 150, label: "R150" },
];

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [lastResult, setLastResult] = useState<ParseResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [rei, setRei] = useState(90);
  const [ogzLoading, setOgzLoading] = useState(false);
  const [ogzResult, setOgzResult] = useState<OgzCalculationResponse | null>(null);

  useEffect(() => {
    if (!id) return;
    getProjectDetails(id)
      .then((data) => setProject(data.project))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const handleParsed = (result: ParseResult & { batch_id: string }) => {
    setLastResult(result);
    setOgzResult(null);
  };

  const handleCalculateOgz = async () => {
    if (!lastResult?.items?.length) {
      message.warning("Сначала загрузите и распознайте PDF");
      return;
    }

    setOgzLoading(true);
    try {
      const requestItems = lastResult.items.map((item) => ({
        mark: item.mark,
        type_name: item.type_name,
        quantity: item.quantity || 1,
        unit_weight_kg: item.unit_weight_kg,
        total_weight_kg: item.total_weight_kg,
        unit_area_m2: item.unit_area_m2,
        total_area_m2: item.total_area_m2,
        ptm: item.ptm,
      }));

      const result = await calculateOgz({
        items: requestItems,
        rei,
        environment: "сухая",
      });

      setOgzResult(result);

      if (result.errors.length > 0) {
        message.warning(`Расчёт завершён с ${result.errors.length} предупреждениями`);
      } else {
        message.success(
          `Расчёт ОГЗ выполнен. Краска: ${result.composition?.kraska_name || "—"}, ` +
          `стоимость: ${result.totals.total_material_cost_rub.toLocaleString("ru-RU")} ₽`
        );
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка расчёта ОГЗ";
      message.error(msg);
    } finally {
      setOgzLoading(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: "block", margin: "100px auto" }} />;

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        onClick={() => navigate("/")}
        style={{ marginBottom: 16 }}
      >
        Назад к проектам
      </Button>

      {project && (
        <Card style={{ marginBottom: 24 }}>
          <Title level={3}>{project.name || project.external_code || "Без названия"}</Title>
          <Descriptions size="small" column={3}>
            <Descriptions.Item label="Шифр">{project.external_code || "-"}</Descriptions.Item>
            <Descriptions.Item label="Стадия">
              {project.stage ? <Tag>{project.stage}</Tag> : "-"}
            </Descriptions.Item>
            <Descriptions.Item label="Создан">
              {new Date(project.created_at).toLocaleDateString("ru-RU")}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      <PdfUploader onParsed={handleParsed} />

      {lastResult && (
        <Card
          title="Результаты парсинга"
          extra={
            <Space>
              <Button
                icon={<DownloadOutlined />}
                href={getExportUrl(lastResult.batch_id!, "json")}
                target="_blank"
              >
                JSON
              </Button>
              <Button
                icon={<DownloadOutlined />}
                href={getExportUrl(lastResult.batch_id!, "csv")}
                target="_blank"
              >
                CSV
              </Button>
              <Button
                icon={<DownloadOutlined />}
                href={getExportUrl(lastResult.batch_id!, "xlsx")}
                target="_blank"
              >
                Excel
              </Button>
            </Space>
          }
        >
          <div style={{ marginBottom: 16 }}>
            <Space>
              <Text>Файл: {lastResult.source_file}</Text>
              <Tag color="green">{(lastResult.success_rate * 100).toFixed(0)}% распознано</Tag>
              {lastResult.errors.length > 0 && (
                <Tag color="red">{lastResult.errors.length} ошибок</Tag>
              )}
            </Space>
          </div>

          <Card
            size="small"
            title="Расчёт ОГЗ"
            style={{ marginBottom: 16, background: "#fafafa" }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
              <Text strong>Предел огнестойкости:</Text>
              <Select
                value={rei}
                onChange={setRei}
                options={REI_OPTIONS}
                style={{ width: 100 }}
              />
              <Button
                type="primary"
                icon={<CalculatorOutlined />}
                loading={ogzLoading}
                onClick={handleCalculateOgz}
              >
                Рассчитать объёмы
              </Button>
            </div>
            {ogzResult?.composition && (
              <div style={{ marginTop: 12 }}>
                <Space wrap>
                  <Tag color="blue">REI {ogzResult.composition.rei_minutes}</Tag>
                  <Tag>Грунт: {ogzResult.composition.grunt_name}</Tag>
                  <Tag>Краска: {ogzResult.composition.kraska_name}</Tag>
                  <Tag>Финиш: {ogzResult.composition.finish_name}</Tag>
                </Space>
              </div>
            )}
            {ogzResult?.errors && ogzResult.errors.length > 0 && (
              <div style={{ marginTop: 8 }}>
                {ogzResult.errors.map((e, i) => (
                  <Tag color="orange" key={i} style={{ marginBottom: 4 }}>
                    {e}
                  </Tag>
                ))}
              </div>
            )}
          </Card>

          <Tabs
            items={[
              {
                key: "items",
                label: `Строки ведомости (${lastResult.items.length})`,
                children: (
                  <LineItemsTable
                    items={lastResult.items}
                    ogzResults={ogzResult?.positions}
                    ogzTotals={ogzResult?.totals}
                    ogzKraskaName={ogzResult?.composition?.kraska_name}
                  />
                ),
              },
              {
                key: "unrecognized",
                label: `Нераспознанные (${lastResult.unrecognized_rows.length})`,
                children:
                  lastResult.unrecognized_rows.length > 0 ? (
                    <pre style={{ maxHeight: 400, overflow: "auto", fontSize: 12 }}>
                      {JSON.stringify(lastResult.unrecognized_rows, null, 2)}
                    </pre>
                  ) : (
                    <Text type="success">Все строки распознаны успешно</Text>
                  ),
              },
            ]}
          />
        </Card>
      )}
    </div>
  );
}
