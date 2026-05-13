import { useEffect, useState } from "react";
import {
  Card,
  Tabs,
  Form,
  Input,
  Switch,
  Select,
  Slider,
  InputNumber,
  Button,
  Typography,
  Space,
  message,
  Spin,
  Divider,
  Tag,
} from "antd";
import {
  ApiOutlined,
  KeyOutlined,
  RobotOutlined,
  SettingOutlined,
  SaveOutlined,
  UndoOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import {
  getSettings,
  updateAiProviderConfig,
  updateAdminSettings,
  resetSettings,
} from "../services/api";
import type {
  AppSettings,
  AiProviderConfig,
  AdminSettings,
  AiProviderModel,
} from "../types";
import { setAppName, setCompanyName } from "../services/state";

const { Title, Text } = Typography;

const DEEPSEEK_MODELS: AiProviderModel[] = [
  { model_id: "deepseek-chat", display_name: "DeepSeek Chat (V3)", max_tokens: 65536 },
  { model_id: "deepseek-reasoner", display_name: "DeepSeek Reasoner (R1)", max_tokens: 65536 },
];

const CLAUDE_MODELS: AiProviderModel[] = [
  { model_id: "claude-sonnet-4-20250514", display_name: "Claude Sonnet 4", max_tokens: 200000 },
  { model_id: "claude-3-5-sonnet-20241022", display_name: "Claude 3.5 Sonnet", max_tokens: 200000 },
  { model_id: "claude-3-opus-20240229", display_name: "Claude 3 Opus", max_tokens: 200000 },
  { model_id: "claude-3-haiku-20240307", display_name: "Claude 3 Haiku", max_tokens: 200000 },
];

function AiProviderForm({
  provider,
  config,
  models,
  onSave,
  loading,
}: {
  provider: string;
  config: AiProviderConfig | null;
  models: AiProviderModel[];
  onSave: (key: string, cfg: AiProviderConfig) => Promise<void>;
  loading: boolean;
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (config) {
      form.setFieldsValue(config);
    }
  }, [config, form]);

  const handleSave = async () => {
    const values = await form.validateFields();
    const modelDef = models.find((m) => m.model_id === values.model);
    const updated: AiProviderConfig = {
      ...values,
      available_models: models,
      max_tokens: modelDef?.max_tokens ?? values.max_tokens,
    };
    await onSave(provider, updated);
  };

  if (!config) return <Spin />;

  return (
    <Form form={form} layout="vertical" initialValues={config}>
      <Form.Item label="Включить провайдера" name="enabled" valuePropName="checked">
        <Switch checkedChildren="Вкл" unCheckedChildren="Выкл" />
      </Form.Item>

      <Form.Item
        label="API Key"
        name="api_key"
        rules={[{ required: false }]}
        extra="Ключ хранится локально в settings.json на сервере"
      >
        <Input.Password
          prefix={<KeyOutlined />}
          placeholder="sk-..."
          visibilityToggle
        />
      </Form.Item>

      <Form.Item
        label="API Base URL"
        name="api_base"
        rules={[{ required: true, message: "Укажите базовый URL" }]}
      >
        <Input prefix={<ApiOutlined />} placeholder="https://api.deepseek.com/v1" />
      </Form.Item>

      <Form.Item
        label="Модель"
        name="model"
        rules={[{ required: true, message: "Выберите модель" }]}
      >
        <Select
          options={models.map((m) => ({
            value: m.model_id,
            label: (
              <Space>
                {m.display_name}
                <Tag>{m.max_tokens.toLocaleString()} токенов</Tag>
              </Space>
            ),
          }))}
        />
      </Form.Item>

      <Form.Item label="Temperature" name="temperature">
        <Slider min={0} max={2} step={0.1} marks={{ 0: "0", 0.5: "0.5", 1: "1", 1.5: "1.5", 2: "2" }} />
      </Form.Item>

      <Form.Item label="Max Tokens" name="max_tokens">
        <InputNumber min={1} max={200000} style={{ width: "100%" }} />
      </Form.Item>

      <Button
        type="primary"
        icon={<SaveOutlined />}
        onClick={handleSave}
        loading={loading}
        block
      >
        Сохранить настройки {provider === "deepseek" ? "DeepSeek" : "Claude"}
      </Button>
    </Form>
  );
}

function AdminForm({
  config,
  onSave,
  loading,
}: {
  config: AdminSettings | null;
  onSave: (cfg: AdminSettings) => Promise<void>;
  loading: boolean;
}) {
  const [form] = Form.useForm();

  useEffect(() => {
    if (config) {
      form.setFieldsValue(config);
    }
  }, [config, form]);

  const handleSave = async () => {
    const values = await form.validateFields();
    await onSave(values);
  };

  if (!config) return <Spin />;

  return (
    <Form form={form} layout="vertical" initialValues={config}>
      <Form.Item
        label="Название приложения"
        name="app_name"
        rules={[{ required: true }]}
      >
        <Input />
      </Form.Item>

      <Form.Item label="Название компании" name="company_name">
        <Input placeholder="ООО ..." />
      </Form.Item>

      <Form.Item
        label="Макс. размер загрузки (МБ)"
        name="max_upload_size_mb"
        rules={[{ required: true }]}
      >
        <InputNumber min={1} max={500} style={{ width: "100%" }} />
      </Form.Item>

      <Form.Item label="Валюта по умолчанию" name="default_currency">
        <Select
          options={[
            { value: "RUB", label: "₽ RUB" },
            { value: "USD", label: "$ USD" },
            { value: "EUR", label: "€ EUR" },
          ]}
        />
      </Form.Item>

      <Form.Item label="Среда по умолчанию" name="default_environment">
        <Select
          options={[
            { value: "сухая", label: "Сухая" },
            { value: "влажная", label: "Влажная" },
            { value: "агрессивная", label: "Агрессивная" },
          ]}
        />
      </Form.Item>

      <Form.Item label="Авто-резервное копирование" name="auto_backup_enabled" valuePropName="checked">
        <Switch />
      </Form.Item>

      <Form.Item label="Интервал бэкапа (часов)" name="backup_interval_hours">
        <InputNumber min={1} max={168} style={{ width: "100%" }} />
      </Form.Item>

      <Form.Item label="Режим отладки" name="debug_mode" valuePropName="checked">
        <Switch />
      </Form.Item>

      <Form.Item label="Уровень логирования" name="log_level">
        <Select
          options={[
            { value: "DEBUG", label: "DEBUG" },
            { value: "INFO", label: "INFO" },
            { value: "WARNING", label: "WARNING" },
            { value: "ERROR", label: "ERROR" },
          ]}
        />
      </Form.Item>

      <Form.Item label="Язык интерфейса" name="language">
        <Select
          options={[
            { value: "ru", label: "Русский" },
            { value: "en", label: "English" },
          ]}
        />
      </Form.Item>

      <Button
        type="primary"
        icon={<SaveOutlined />}
        onClick={handleSave}
        loading={loading}
        block
      >
        Сохранить настройки администратора
      </Button>
    </Form>
  );
}

export default function SettingsPage() {
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [lastModified, setLastModified] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState("deepseek");

  const loadSettings = () => {
    setLoading(true);
    getSettings()
      .then((res) => {
        setSettings(res.settings);
        setLastModified(res.last_modified ?? null);
      })
      .catch(() => message.error("Не удалось загрузить настройки"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const saveProvider = async (provider: string, config: AiProviderConfig) => {
    setSaving(true);
    try {
      await updateAiProviderConfig(provider, config);

      setSettings((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          ai_providers: {
            ...prev.ai_providers,
            [provider]: { ...prev.ai_providers[provider as keyof typeof prev.ai_providers], ...config },
          },
        };
      });
      message.success(`${provider === "deepseek" ? "DeepSeek" : "Claude"}: настройки сохранены`);
    } catch {
      message.error("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const saveAdmin = async (admin: AdminSettings) => {
    setSaving(true);
    try {
      await updateAdminSettings(admin);
      setSettings((prev) => (prev ? { ...prev, admin } : prev));
      setAppName(admin.app_name);
      setCompanyName(admin.company_name);
      message.success("Администраторские настройки сохранены");
    } catch {
      message.error("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    try {
      await resetSettings();
      message.success("Настройки сброшены к заводским");
      loadSettings();
    } catch {
      message.error("Ошибка сброса");
    }
  };

  const tabItems = [
    {
      key: "deepseek",
      label: (
        <span>
          <RobotOutlined /> DeepSeek
        </span>
      ),
      children: settings ? (
        <AiProviderForm
          provider="deepseek"
          config={settings.ai_providers.deepseek}
          models={DEEPSEEK_MODELS}
          onSave={saveProvider}
          loading={saving}
        />
      ) : null,
    },
    {
      key: "claude",
      label: (
        <span>
          <RobotOutlined /> Claude
        </span>
      ),
      children: settings ? (
        <AiProviderForm
          provider="claude"
          config={settings.ai_providers.claude}
          models={CLAUDE_MODELS}
          onSave={saveProvider}
          loading={saving}
        />
      ) : null,
    },
    {
      key: "admin",
      label: (
        <span>
          <SettingOutlined /> Администрирование
        </span>
      ),
      children: settings ? (
        <AdminForm config={settings.admin} onSave={saveAdmin} loading={saving} />
      ) : null,
    },
  ];

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          Настройки
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadSettings} loading={loading}>
            Обновить
          </Button>
          <Button icon={<UndoOutlined />} danger onClick={handleReset}>
            Сбросить к заводским
          </Button>
        </Space>
      </div>

      {lastModified && (
        <Text type="secondary" style={{ display: "block", marginBottom: 16 }}>
          Последнее изменение: {lastModified}
        </Text>
      )}

      <Divider style={{ marginTop: 0 }} />

      {loading ? (
        <div style={{ textAlign: "center", padding: 48 }}>
          <Spin size="large" />
        </div>
      ) : (
        <Tabs activeKey={tab} onChange={setTab} items={tabItems} />
      )}
    </Card>
  );
}
