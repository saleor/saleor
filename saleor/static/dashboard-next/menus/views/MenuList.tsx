import * as React from "react";

import { menuAddUrl, menuListUrl, menuUrl } from "..";
import ErrorMessageCard from "../../components/ErrorMessageCard";
import Navigator from "../../components/Navigator";
import { MenuListQuery } from "../../gql-types";
import i18n from "../../i18n";
import { createPaginationData, createPaginationState } from "../../misc";
import MenuListPage from "../components/MenuListPage";
import { menuListQuery, TypedMenuListQuery } from "../queries";

interface MenuListProps {
  params: {
    after?: string;
    before?: string;
  };
}

const PAGINATE_BY = 20;

const unrollMenuConnection = (data: MenuListQuery) =>
  data && data.menus && data.menus.edges
    ? data.menus.edges.map(edge => edge.node)
    : undefined;

export const MenuList: React.StatelessComponent<MenuListProps> = ({
  params
}) => (
  <Navigator>
    {navigate => {
      const paginationState = createPaginationState(PAGINATE_BY, params);
      return (
        <TypedMenuListQuery query={menuListQuery} variables={paginationState}>
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
              data && data.menus ? data.menus.pageInfo : undefined,
              loading
            );
            return (
              <MenuListPage
                disabled={loading}
                menus={unrollMenuConnection(data)}
                onAdd={() => navigate(menuAddUrl)}
                onNextPage={loadNextPage}
                onPreviousPage={loadPreviousPage}
                pageInfo={pageInfo}
                onRowClick={id => () => navigate(menuUrl(id))}
              />
            );
          }}
        </TypedMenuListQuery>
      );
    }}
  </Navigator>
);
export default MenuList;
