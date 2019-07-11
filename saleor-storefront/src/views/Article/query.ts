import gql from "graphql-tag";

import { TypedQuery } from "../../core/queries";
import { Article, ArticleVariables } from "./types/Article";

const articleQuery = gql`
  query Article($slug: String!) {
    page(slug: $slug) {
      content
      id
      seoDescription
      seoTitle
      slug
      title
    }
    shop {
      homepageCollection {
        id
        backgroundImage {
          url
        }
      }
    }
  }
`;

export const TypedArticleQuery = TypedQuery<Article, ArticleVariables>(
  articleQuery
);
