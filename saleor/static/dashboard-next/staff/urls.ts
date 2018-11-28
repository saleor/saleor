import * as urlJoin from "url-join";

const staffSection = "/staff/";

export const staffListPath = staffSection;
export const staffListUrl = staffListPath;

export const staffMemberAddPath = urlJoin(staffSection, "add");
export const staffMemberAddUrl = staffMemberAddPath;

export const staffMemberDetailsPath = (id: string) => urlJoin(staffSection, id);
export const staffMemberDetailsUrl = (id: string) =>
  staffMemberDetailsPath(encodeURIComponent(id));

export const staffMemberRemovePath = (id: string) =>
  urlJoin(staffMemberDetailsPath(id), "remove");
export const staffMemberRemoveUrl = (id: string) =>
  staffMemberRemovePath(encodeURIComponent(id));
