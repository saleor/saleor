import * as urlJoin from "url-join";
import { categoryPath } from "../../urls";

export const categoryDeletePath = (id: string) =>
  urlJoin(categoryPath(id), "delete");
export const categoryDeleteUrl = (id: string) =>
  categoryDeletePath(encodeURIComponent(id));
