export interface Medium {
  ariaLabel: string;
  iconName:
    | "social_facebook"
    | "social_instagram"
    | "social_twitter"
    | "social_youtube";
  href: string;
}

export interface IProps {
  medium: Medium;
  target?: string;
}
