import { content } from "../storybook/stories/components/RichTextEditor";
import { PageDetails_page } from "./types/PageDetails";
import { PageList_pages_edges_node } from "./types/PageList";

export const pageList: PageList_pages_edges_node[] = [
  {
    __typename: "Page",
    id: "Jzx123sEt==",
    isVisible: true,
    slug: "about",
    title: "About"
  },
  {
    __typename: "Page",
    id: "Jzx123sEx==",
    isVisible: false,
    slug: "about",
    title: "About"
  },
  {
    __typename: "Page",
    id: "Jzx123sEu==",
    isVisible: true,
    slug: "about",
    title: "About"
  },
  {
    __typename: "Page",
    id: "Jzx123sEm==",
    isVisible: true,
    slug: "about",
    title: "About"
  }
];
export const page: PageDetails_page = {
  __typename: "Page",
  availableOn: "",
  contentJson: JSON.stringify(content),
  id: "Kzx152sEm==",
  isVisible: false,
  seoDescription: "About",
  seoTitle: "About",
  slug: "about",
  title: "About"
};
