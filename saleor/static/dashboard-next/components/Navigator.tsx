import * as invariant from "invariant";
import * as PropTypes from "prop-types";
import * as React from "react";

interface NavigatorProps {
  children: ((
    navigate: (url: string, replace?: boolean, preserveQs?: boolean) => any
  ) => React.ReactElement<any>);
}

const Navigator: React.StatelessComponent<NavigatorProps> = (
  { children },
  { router }
) => {
  invariant(router, "You should not use <Navigator> outside a <Router>");
  const {
    history,
    route: {
      location: { search }
    }
  } = router;
  const navigate = (url, replace = false, preserveQs = false) => {
    const targetUrl = preserveQs ? url + search : url;
    replace ? history.replace(targetUrl) : history.push(targetUrl);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return children(navigate);
};
Navigator.contextTypes = {
  router: PropTypes.shape({
    history: PropTypes.shape({
      push: PropTypes.func.isRequired,
      replace: PropTypes.func.isRequired
    }).isRequired
  })
};
Navigator.displayName = "Navigator";

interface NavigatorLinkProps {
  replace?: boolean;
  to: string;
  children: ((navigate: () => any) => React.ReactElement<any>);
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
