import { stringify as stringifyQs } from "qs";
import * as React from "react";

import { createPaginationState } from "../../components/Paginator";
import useNavigator from "../../hooks/useNavigator";
import usePaginator from "../../hooks/usePaginator";
import useShop from "../../hooks/useShop";
import { maybe } from "../../misc";
import { Pagination } from "../../types";
import TranslationsEntitiesList from "../components/TranslationsEntitiesList";
import TranslationsEntitiesListPage, {
  TranslationsEntitiesListFilterTab
} from "../components/TranslationsEntitiesListPage";
import {
  TypedCategoryTranslations,
  TypedProductTranslations
} from "../queries";
import {
  languageEntityUrl,
  languageListUrl,
  TranslatableEntities
} from "../urls";

export type TranslationsEntitiesListQueryParams = Pagination & {
  tab: TranslationsEntitiesListFilterTab;
};

interface TranslationsEntitiesProps {
  language: string;
  params: TranslationsEntitiesListQueryParams;
}

const PAGINATE_BY = 20;

const TranslationsEntities: React.FC<TranslationsEntitiesProps> = ({
  language,
  params
}) => {
  const navigate = useNavigator();
  const paginate = usePaginator();
  const shop = useShop();

  if (Object.keys(TranslatableEntities).indexOf(params.tab) === -1) {
    navigate(
      "?" +
        stringifyQs({
          tab: TranslatableEntities.categories
        }),
      true
    );
  }

  const filterCallbacks = {
    onCategoriesTabClick: () =>
      navigate(
        "?" +
          stringifyQs({
            tab: TranslatableEntities.categories
          })
      ),
    onProductsTabClick: () =>
      navigate(
        "?" +
          stringifyQs({
            tab: TranslatableEntities.products
          })
      )
  };
  const lang = maybe(() =>
    shop.languages.find(languageFromList => languageFromList.code === language)
  );
  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <TranslationsEntitiesListPage
      filters={{
        current: params.tab,
        ...filterCallbacks
      }}
      language={lang}
      onBack={() => navigate(languageListUrl)}
    >
      {params.tab === "categories" ? (
        <TypedCategoryTranslations
          variables={{ language: language as any, ...paginationState }}
        >
          {({ data, loading }) => {
            const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
              maybe(() => data.categories.pageInfo),
              paginationState,
              params
            );

            return (
              <TranslationsEntitiesList
                disabled={loading}
                entities={maybe(() =>
                  data.categories.edges
                    .map(edge => edge.node)
                    .map(node => ({
                      completion: {
                        current: node.translation
                          ? [
                              node.translation.descriptionJson,
                              node.translation.name,
                              node.translation.seoDescription,
                              node.translation.seoTitle
                            ].reduce(
                              (acc, field) => acc + (field !== null ? 1 : 0)
                            )
                          : 0,
                        max: 4
                      },
                      id: node.id,
                      name: node.name
                    }))
                )}
                onRowClick={id =>
                  navigate(
                    languageEntityUrl(
                      language,
                      TranslatableEntities.categories,
                      id
                    )
                  )
                }
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
              />
            );
          }}
        </TypedCategoryTranslations>
      ) : params.tab === "products" ? (
        <TypedProductTranslations
          variables={{ language: language as any, ...paginationState }}
        >
          {({ data, loading }) => {
            const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
              maybe(() => data.products.pageInfo),
              paginationState,
              params
            );

            return (
              <TranslationsEntitiesList
                disabled={loading}
                entities={maybe(() =>
                  data.products.edges
                    .map(edge => edge.node)
                    .map(node => ({
                      completion: {
                        current: node.translation
                          ? [
                              node.translation.descriptionJson,
                              node.translation.name,
                              node.translation.seoDescription,
                              node.translation.seoTitle
                            ].reduce(
                              (acc, field) => acc + (field !== null ? 1 : 0)
                            )
                          : 0,
                        max: 4
                      },
                      id: node.id,
                      name: node.name
                    }))
                )}
                onRowClick={id =>
                  navigate(
                    languageEntityUrl(
                      language,
                      TranslatableEntities.products,
                      id
                    )
                  )
                }
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
              />
            );
          }}
        </TypedProductTranslations>
      ) : null}
    </TranslationsEntitiesListPage>
  );
};
TranslationsEntities.displayName = "TranslationsEntities";
export default TranslationsEntities;
