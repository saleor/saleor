import "./scss/index.scss";

import * as React from "react";
import { RouteComponentProps } from "react-router";

import { Authenticated } from "../../components";
import Page from "./Page";
import {
  TypedOrderDetailsByIdQuery,
  TypedOrderDetailsByTokenQuery
} from "./queries";

const View: React.FC<RouteComponentProps<{ id?: string; token?: string }>> = ({
  match: {
    params: { id, token },
  },
}) => {
  const guest = !id;

  return (
    <div className="order-details container">
      {guest ? (
        <TypedOrderDetailsByTokenQuery variables={{ token }}>
          {({ data: { orderByToken } }) => <Page guest order={orderByToken} />}
        </TypedOrderDetailsByTokenQuery>
      ) : (
        <TypedOrderDetailsByIdQuery variables={{ id }}>
          {({ data: { order } }) => (
            <Authenticated>
              <Page guest={false} order={order} />
            </Authenticated>
          )}
        </TypedOrderDetailsByIdQuery>
      )}
    </div>
  );
};

export default View;
