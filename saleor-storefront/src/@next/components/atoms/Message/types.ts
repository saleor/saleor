export interface IProps {
  title: string;
  status?: "neutral" | "success" | "error" | "action";
  onClick: () => void;
  children?: React.ReactNode;
  actionText?: string;
}
