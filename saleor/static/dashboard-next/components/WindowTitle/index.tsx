import * as React from "react";
import { Helmet } from "react-helmet";

import Shop from "../Shop";

interface WindowTitleProps {
  title: string;
}

export const WindowTitle: React.StatelessComponent<WindowTitleProps> = ({
  title
}) => (
  <Shop>
    {shop =>
      shop === undefined || !title ? null : (
        <Helmet>
          <title>{`${title} | ${shop.name}`}</title>
        </Helmet>
      )
    }
  </Shop>
);
