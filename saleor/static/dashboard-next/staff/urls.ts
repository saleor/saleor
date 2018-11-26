import * as urlJoin from "url-join";

const staffSection = "/staff/";
export const staffListUrl = staffSection;
export const staffMemberAddUrl = urlJoin(staffSection, "add");
export const staffMemberDetailsUrl = (id: string) => urlJoin(staffSection, id);
export const staffMemberRemoveUrl = (id: string) =>
  urlJoin(staffMemberDetailsUrl(id), "remove");
