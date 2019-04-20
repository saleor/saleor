import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { BulkAction, Dialog, Pagination } from "../types";

const staffSection = "/staff/";

export const staffListPath = staffSection;
export type StaffListUrlDialog = "add" | "remove";
export type StaffListUrlQueryParams = BulkAction &
  Dialog<StaffListUrlDialog> &
  Pagination;
export const staffListUrl = (params?: StaffListUrlQueryParams) =>
  staffListPath + "?" + stringifyQs(params);

export const staffMemberDetailsPath = (id: string) => urlJoin(staffSection, id);
export type StaffMemberDetailsUrlDialog = "remove";
export type StaffMemberDetailsUrlQueryParams = Dialog<
  StaffMemberDetailsUrlDialog
>;
export const staffMemberDetailsUrl = (
  id: string,
  params?: StaffMemberDetailsUrlQueryParams
) => staffMemberDetailsPath(encodeURIComponent(id)) + "?" + stringifyQs(params);
