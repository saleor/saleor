import * as React from "react";

import { menuItemAddUrl, menuItemUrl, menuListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { MenuItemDetailsQuery } from "../../gql-types";
import i18n from "../../i18n";
import { createPaginationData, createPaginationState } from "../../misc";
import MenuItemDetailsPage from "../components/MenuItemDetailsPage";
import { menuItemDetailsQuery, TypedMenuItemDetailsQuery } from "../queries";

interface MenuItemDetailsProps {
  id: string;
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

const unrollMenuItemsConnection = (data: MenuItemDetailsQuery) =>
  data &&
  data.menuItem &&
  data.menuItem.children &&
  data.menuItem.children.edges
    ? data.menuItem.children.edges.map(edge => edge.node)
    : undefined;

export const MenuItemDetails: React.StatelessComponent<
  MenuItemDetailsProps
> = ({ id, params }) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedMenuItemDetailsQuery
          query={menuItemDetailsQuery}
          variables={{ id, ...paginationState }}
        >
          {({ data, loading, error }) => {
            if (error) {
              return (
                <ErrorMessageCard
                  message={i18n.t("Something went terribly wrong")}
                />
              );
            }
            const {
              loadNextPage,
              loadPreviousPage,
              pageInfo
            } = createPaginationData(
              navigate,
              paginationState,
              menuListUrl,
              data && data.menuItem && data.menuItem.children
                ? data.menuItem.children.pageInfo
                : undefined,
              loading
            );
            return (
              <MenuItemDetailsPage
                disabled={loading}
                menuItem={data ? data.menuItem : undefined}
                menuItems={unrollMenuItemsConnection(data)}
                onBack={() => navigate(menuListUrl)}
                onAdd={() => navigate(menuItemAddUrl)}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
                onRowClick={id => () => navigate(menuItemUrl(id))}
              />
            );
          }}
        </TypedMenuItemDetailsQuery>
      );
    }}
  </Navigator>
);
export default MenuItemDetails;
