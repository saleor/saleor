import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
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
import TableRow from "@material-ui/core/TableRow";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActions, ListProps } from "../../../types";
import { PageList_pages_edges_node } from "../../types/PageList";

export interface PageListProps extends ListProps, ListActions {
  pages: PageList_pages_edges_node[];
}

const styles = (theme: Theme) =>
  createStyles({
    [theme.breakpoints.up("lg")]: {
      colSlug: {
        width: 250
      },
      colTitle: {},
      colVisibility: {
        width: 200
      }
    },
    colSlug: {},
    colTitle: {},
    colVisibility: {},
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
    onPreviousPage,
    isChecked,
    selected,
    toggle,
    toolbar
  }: PageListProps & WithStyles<typeof styles>) => (
    <Card>
      <Table>
        <TableHead selected={selected} toolbar={toolbar}>
          <TableRow>
            <TableCell />
            <TableCell className={classes.colTitle} padding="dense">
              {i18n.t("Title", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colSlug} padding="dense">
              {i18n.t("Slug", { context: "table header" })}
            </TableCell>
            <TableCell className={classes.colVisibility} padding="dense">
              {i18n.t("Visibility", { context: "table header" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={4}
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
            page => {
              const isSelected = page ? isChecked(page.id) : false;

              return (
                <TableRow
                  hover={!!page}
                  className={!!page ? classes.link : undefined}
                  onClick={page ? onRowClick(page.id) : undefined}
                  key={page ? page.id : "skeleton"}
                  selected={isSelected}
                >
                  <TableCell padding="checkbox">
                    <Checkbox
                      color="primary"
                      checked={isSelected}
                      disabled={disabled}
                      onClick={event => {
                        toggle(page.id);
                        event.stopPropagation();
                      }}
                    />
                  </TableCell>
                  <TableCell className={classes.colTitle}>
                    {maybe<React.ReactNode>(() => page.title, <Skeleton />)}
                  </TableCell>
                  <TableCell className={classes.colSlug}>
                    {maybe<React.ReactNode>(() => page.slug, <Skeleton />)}
                  </TableCell>
                  <TableCell className={classes.colVisibility}>
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
              );
            },
            () => (
              <TableRow>
                <TableCell colSpan={4}>{i18n.t("No pages found")}</TableCell>
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
