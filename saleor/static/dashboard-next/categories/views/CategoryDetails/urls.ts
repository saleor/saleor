import * as urlJoin from "url-join";
import { categoryUrl } from "../../urls";

export const categoryDeleteUrl = (id: string) =>
  urlJoin(categoryUrl(id), "delete");
