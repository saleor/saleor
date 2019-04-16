import { stringify as stringifyQs } from "qs";
import * as urlJoin from "url-join";

import { Dialog } from "../types";

export const pagesSection = "/pages/";

export const pageListPath = pagesSection;
export const pageListUrl = pageListPath;

export const pagePath = (id: string) => urlJoin(pagesSection, id);
export type PageUrlDialog = "remove";
export type PageUrlQueryParams = Dialog<PageUrlDialog>;
export const pageUrl = (id: string, params?: PageUrlQueryParams) =>
  pagePath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const pageCreatePath = urlJoin(pagesSection, "add");
export const pageCreateUrl = pageCreatePath;
