import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Typography, Descriptions, Tag, Button, Space, Spin, Tabs } from "antd";
import { ArrowLeftOutlined, DownloadOutlined } from "@ant-design/icons";
import { getProjectDetails, getExportUrl } from "../services/api";
import PdfUploader from "../components/PdfUploader";
import LineItemsTable from "../components/LineItemsTable";
import type { ParseResult, Project } from "../types";

const { Title, Text } = Typography;

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [lastResult, setLastResult] = useState<ParseResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    getProjectDetails(id)
      .then((data) => setProject(data.project))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const handleParsed = (result: ParseResult & { batch_id: string }) => {
    setLastResult(result);
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

          <Tabs
            items={[
              {
                key: "items",
                label: `Строки ведомости (${lastResult.items.length})`,
                children: <LineItemsTable items={lastResult.items} />,
              },
              {
                key: "unrecognized",
                label: `Нераспознанные (${lastResult.unrecognized_rows.length})`,
                children: lastResult.unrecognized_rows.length > 0 ? (
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
