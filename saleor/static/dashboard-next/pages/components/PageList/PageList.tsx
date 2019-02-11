import Card from "@material-ui/core/Card";
import {
  createStyles,
  Theme,
  withStyles,
  WithStyles
} from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableHead from "@material-ui/core/TableHead";
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { PageList_pages_edges_node } from "../../types/PageList";

export interface PageListProps extends ListProps {
  pages: PageList_pages_edges_node[];
}

const styles = createStyles({
  link: {
    cursor: "pointer"
  }
});
const PageList = withStyles(styles, { name: "PageList" })(
  ({
    classes,
    pages,
    disabled,
    onNextPage,
    pageInfo,
    onRowClick,
    onPreviousPage
  }: PageListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell padding="dense">
              {i18n.t("Title", { context: "table header" })}
            </TableCell>
            <TableCell padding="dense">
              {i18n.t("Slug", { context: "table header" })}
            </TableCell>
            <TableCell padding="dense">
              {i18n.t("Visibility", { context: "table header" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={pageInfo && !disabled ? pageInfo.hasNextPage : false}
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : false
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            pages,
            page => (
              <TableRow
                hover={!!page}
                className={!!page ? classes.link : undefined}
                onClick={page ? onRowClick(page.id) : undefined}
                key={page ? page.id : "skeleton"}
              >
                <TableCell>
                  {maybe<React.ReactNode>(() => page.title, <Skeleton />)}
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(() => page.slug, <Skeleton />)}
                </TableCell>
                <TableCell>
                  {maybe<React.ReactNode>(
                    () => (
                      <StatusLabel
                        label={
                          page.isVisible
                            ? i18n.t("Published")
                            : i18n.t("Not Published")
                        }
                        status={page.isVisible ? "success" : "error"}
                      />
                    ),
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={3}>{i18n.t("No pages found")}</TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
PageList.displayName = "PageList";
export default PageList;
