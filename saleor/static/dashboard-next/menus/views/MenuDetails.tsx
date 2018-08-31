import * as React from "react";

import { menuItemAddUrl, menuItemUrl, menuListUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { MenuDetailsQuery } from "../../gql-types";
import i18n from "../../i18n";
import { createPaginationData, createPaginationState } from "../../misc";
import MenuDetailsPage from "../components/MenuDetailsPage";
import { menuDetailsQuery, TypedMenuDetailsQuery } from "../queries";

interface MenuDetailsProps {
  id: string;
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

const unrollMenuItemsConnection = (data: MenuDetailsQuery) =>
  data && data.menu && data.menu.items && data.menu.items.edges
    ? data.menu.items.edges.map(edge => edge.node)
    : undefined;

export const MenuDetails: React.StatelessComponent<MenuDetailsProps> = ({
  id,
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedMenuDetailsQuery
          query={menuDetailsQuery}
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
              data && data.menu && data.menu.items
                ? data.menu.items.pageInfo
                : undefined,
              loading
            );
            return (
              <MenuDetailsPage
                disabled={loading}
                menu={data ? data.menu : undefined}
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
        </TypedMenuDetailsQuery>
      );
    }}
  </Navigator>
);
export default MenuDetails;
