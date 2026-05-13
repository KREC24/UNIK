import { Upload, Button, Card, Progress, Typography, message } from "antd";
import { InboxOutlined, FilePdfOutlined } from "@ant-design/icons";
import { useState } from "react";
import { uploadPdf } from "../services/api";
import type { ParseResult } from "../types";

const { Dragger } = Upload;
const { Text } = Typography;

interface Props {
  onParsed: (result: ParseResult & { batch_id: string }) => void;
}

export default function PdfUploader({ onParsed }: Props) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [fileName, setFileName] = useState("");

  const handleUpload = async (file: File) => {
    setUploading(true);
    setFileName(file.name);
    setProgress(0);
    try {
      const result = await uploadPdf(file, undefined, setProgress);
      message.success(`Распознано ${result.total_rows_parsed} строк (${(result.success_rate * 100).toFixed(0)}%)`);
      onParsed(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка загрузки";
      message.error(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card title="Загрузка PDF" style={{ marginBottom: 24 }}>
      <Dragger
        accept=".pdf"
        maxCount={1}
        showUploadList={false}
        beforeUpload={(file) => {
          handleUpload(file);
          return false;
        }}
        disabled={uploading}
      >
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">Нажмите или перетащите PDF-файл</p>
        <p className="ant-upload-hint">Поддерживаются листы КМД, ведомости, общие данные</p>
      </Dragger>
      {uploading && (
        <div style={{ marginTop: 16 }}>
          <Text>
            <FilePdfOutlined /> {fileName}
          </Text>
          <Progress percent={progress} status="active" />
        </div>
      )}
    </Card>
  );
}
