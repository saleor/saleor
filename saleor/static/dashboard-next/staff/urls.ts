import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { Dialog, Pagination } from "../types";

const staffSection = "/staff/";

export const staffListPath = staffSection;
export type StaffListUrlDialog = "add";
export type StaffListUrlQueryParams = Dialog<StaffListUrlDialog> & Pagination;
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
