type NotificationTypes = "error" | "success";

interface IMessage {
  title: string;
  content?: string;
}

interface IOptions {
  type: NotificationTypes;
}

export interface INotificationTemplate {
  id: string;
  style: React.CSSProperties;
  message: IMessage;
  options: IOptions;
  close: () => void;
}
