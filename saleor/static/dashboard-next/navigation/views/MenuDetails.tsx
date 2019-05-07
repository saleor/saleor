import * as React from "react";

import { SearchProductsProvider } from "../../containers/SearchProducts";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import { maybe } from "../../misc";
import { CategorySearchProvider } from "../../products/containers/CategorySearch";
import { CollectionSearchProvider } from "../../products/containers/CollectionSearch";
import MenuCreateItemDialog from "../components/MenuCreateItemDialog";
import MenuDetailsPage from "../components/MenuDetailsPage";
import { MenuDetailsQuery } from "../queries";
import { menuListUrl, menuUrl, MenuUrlQueryParams } from "../urls";

interface MenuDetailsProps {
  id: string;
  params: MenuUrlQueryParams;
}

const MenuDetails: React.FC<MenuDetailsProps> = ({ id, params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();

  const closeModal = () =>
    navigate(
      menuUrl(id, {
        ...params,
        action: undefined,
        id: undefined
      }),
      true
    );

  return (
    <MenuDetailsQuery variables={{ id }}>
      {({ data, loading }) => {
        return (
          <>
            <MenuDetailsPage
              disabled={loading}
              menu={maybe(() => data.menu)}
              onBack={() => navigate(menuListUrl())}
              onDelete={() => undefined}
              onItemAdd={() =>
                navigate(
                  menuUrl(id, {
                    action: "add-item"
                  })
                )
              }
              onSubmit={() => undefined}
              saveButtonState="default"
            />
            <CategorySearchProvider>
              {categorySearch => (
                <CollectionSearchProvider>
                  {collectionSearch => (
                    <SearchProductsProvider>
                      {(productSearch, productSearchOpts) => {
                        const handleQueryChange = (query: string) => {
                          categorySearch.search(query);
                          collectionSearch.search(query);
                          productSearch(query);
                        };
                        return (
                          <MenuCreateItemDialog
                            open={params.action === "add-item"}
                            categories={maybe(
                              () =>
                                categorySearch.searchOpts.data.categories.edges.map(
                                  edge => edge.node
                                ),
                              []
                            )}
                            collections={maybe(
                              () =>
                                collectionSearch.searchOpts.data.collections.edges.map(
                                  edge => edge.node
                                ),
                              []
                            )}
                            products={maybe(
                              () =>
                                productSearchOpts.data.products.edges.map(
                                  edge => edge.node
                                ),
                              []
                            )}
                            loading={
                              categorySearch.searchOpts.loading ||
                              collectionSearch.searchOpts.loading ||
                              productSearchOpts.loading
                            }
                            confirmButtonState="default"
                            disabled={false}
                            onClose={closeModal}
                            onSubmit={() => undefined}
                            onQueryChange={handleQueryChange}
                          />
                        );
                      }}
                    </SearchProductsProvider>
                  )}
                </CollectionSearchProvider>
              )}
            </CategorySearchProvider>
          </>
        );
      }}
    </MenuDetailsQuery>
  );
};
MenuDetails.displayName = "MenuDetails";

export default MenuDetails;
