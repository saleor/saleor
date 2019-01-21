import { SaleType } from "../types/globalTypes";
import { SaleList_sales_edges_node } from "./types/SaleList";

export const saleList: SaleList_sales_edges_node[] = [
  {
    __typename: "Sale" as "Sale",
    endDate: null,
    id: "U2FsZTo0",
    name: "Happy front day!",
    startDate: "2019-01-03",
    type: "PERCENTAGE" as SaleType,
    value: 40
  },
  {
    __typename: "Sale" as "Sale",
    endDate: null,
    id: "U2FsZTo1",
    name: "Happy minute day!",
    startDate: "2019-01-03",
    type: "FIXED" as SaleType,
    value: 30
  },
  {
    __typename: "Sale" as "Sale",
    endDate: null,
    id: "U2FsZTox",
    name: "Happy class day!",
    startDate: "2019-01-03",
    type: "PERCENTAGE" as SaleType,
    value: 10
  },
  {
    __typename: "Sale" as "Sale",
    endDate: null,
    id: "U2FsZToy",
    name: "Happy human day!",
    startDate: "2019-01-03",
    type: "PERCENTAGE" as SaleType,
    value: 20
  },
  {
    __typename: "Sale" as "Sale",
    endDate: null,
    id: "U2FsZToz",
    name: "Happy year day!",
    startDate: "2019-01-03",
    type: "PERCENTAGE" as SaleType,
    value: 10
  }
];
