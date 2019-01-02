import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { OrderListQueryParams } from "./views/OrderList";

const orderSectionUrl = "/orders/";

export const orderListPath = orderSectionUrl;
export const orderListUrl = (params?: OrderListQueryParams): string => {
  const orderList = orderSectionUrl;
  if (params === undefined) {
    return orderList;
  } else {
    return urlJoin(orderList, "?" + stringifyQs(params));
  }
};

export const orderPath = (id: string) => urlJoin(orderSectionUrl, id);
export const orderUrl = (id: string) => orderPath(encodeURIComponent(id));
