import * as urlJoin from "url-join";

const pageSectionUrl = "/pages/";
export const pageListUrl = pageSectionUrl;
export const pageUrl = (id: string) => urlJoin(pageSectionUrl, id);
export const pageAddUrl = urlJoin(pageSectionUrl, "add");
