import * as React from "react";

import { createPaginationState } from "../../components/Paginator";
import useNavigator from "../../hooks/useNavigator";
import useNotifier from "../../hooks/useNotifier";
import usePaginator from "../../hooks/usePaginator";
import { maybe } from "../../misc";
import MenuListPage from "../components/MenuListPage";
import { MenuListQuery } from "../queries";
import { menuListUrl, MenuListUrlQueryParams, menuUrl } from "../urls";

const PAGINATE_BY = 20;

interface MenuListProps {
  params: MenuListUrlQueryParams;
}
const MenuList: React.FC<MenuListProps> = ({ params }) => {
  const navigate = useNavigator();
  const notify = useNotifier();
  const paginate = usePaginator();

  const paginationState = createPaginationState(PAGINATE_BY, params);

  return (
    <MenuListQuery variables={paginationState}>
      {({ data, loading }) => {
        const { loadNextPage, loadPreviousPage, pageInfo } = paginate(
          maybe(() => data.menus.pageInfo),
          paginationState,
          params
        );

        return (
          <MenuListPage
            disabled={loading}
            menus={maybe(() => data.menus.edges.map(edge => edge.node))}
            onAdd={() =>
              navigate(
                menuListUrl({
                  action: "add"
                })
              )
            }
            onDelete={id =>
              navigate(
                menuListUrl({
                  action: "remove",
                  id
                })
              )
            }
            onNextPage={loadNextPage}
            onPreviousPage={loadPreviousPage}
            onRowClick={id => () => navigate(menuUrl(id))}
            pageInfo={pageInfo}
          />
        );
      }}
    </MenuListQuery>
  );
};
export default MenuList;
