import * as urlJoin from "url-join";

const staffSection = "/staff/";
export const staffListUrl = staffSection;
export const staffMemberDetailsUrl = (id: string) => urlJoin(staffSection, id);
