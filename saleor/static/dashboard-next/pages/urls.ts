import * as urlJoin from "url-join";

const pageSectionUrl = "/pages/";

export const pageListPath = pageSectionUrl;
export const pageListUrl = pageListPath;

export const pagePath = (id: string) => urlJoin(pageSectionUrl, id);
export const pageUrl = (id: string) => pagePath(encodeURIComponent(id));

export const pageAddPath = urlJoin(pageSectionUrl, "add");
export const pageAddUrl = pageAddPath;
