import * as React from "react";
import { RouteComponentProps, withRouter } from "react-router";

interface NavigatorProps {
  children: (
    navigate: (url: string, replace?: boolean, preserveQs?: boolean) => any
  ) => React.ReactElement<any>;
}

const Navigator = withRouter<NavigatorProps & RouteComponentProps<any>>(
  ({ children, location, history }) => {
    const { search } = location;
    const navigate = (url, replace = false, preserveQs = false) => {
      const targetUrl = preserveQs ? url + search : url;
      replace ? history.replace(targetUrl) : history.push(targetUrl);
      window.scrollTo({ top: 0, behavior: "smooth" });
    };

    return children(navigate);
  }
);
Navigator.displayName = "Navigator";

interface NavigatorLinkProps {
  replace?: boolean;
  to: string;
  children: (navigate: () => any) => React.ReactElement<any>;
}

export const NavigatorLink: React.StatelessComponent<NavigatorLinkProps> = ({
  children,
  replace,
  to
}) => (
  <Navigator>{navigate => children(() => navigate(to, replace))}</Navigator>
);
NavigatorLink.displayName = "NavigatorLink";

export default Navigator;
