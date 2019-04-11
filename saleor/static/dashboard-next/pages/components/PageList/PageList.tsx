import Button from "@material-ui/core/Button";
import Card from "@material-ui/core/Card";
import Checkbox from "@material-ui/core/Checkbox";
import IconButton from "@material-ui/core/IconButton";
import { createStyles, withStyles, WithStyles } from "@material-ui/core/styles";
import Table from "@material-ui/core/Table";
import TableBody from "@material-ui/core/TableBody";
import TableCell from "@material-ui/core/TableCell";
import TableFooter from "@material-ui/core/TableFooter";
import TableRow from "@material-ui/core/TableRow";
import DeleteIcon from "@material-ui/icons/Delete";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import StatusLabel from "../../../components/StatusLabel";
import TableHead from "../../../components/TableHead";
import TablePagination from "../../../components/TablePagination";
import useBulkActions from "../../../hooks/useBulkActions";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListActionProps, ListProps } from "../../../types";
import { PageList_pages_edges_node } from "../../types/PageList";

export interface PageListProps
  extends ListProps,
    ListActionProps<"onBulkDelete" | "onBulkPublish" | "onBulkUnpublish"> {
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
    onBulkDelete,
    onBulkPublish,
    onBulkUnpublish,
    onNextPage,
    pageInfo,
    onRowClick,
    onPreviousPage
  }: PageListProps & WithStyles<typeof styles>) => {
    const { isMember, listElements, toggle } = useBulkActions(pages);

    return (
      <Card>
        <Table>
          <TableHead
            selected={listElements.length}
            toolbar={
              <>
                <Button
                  color="primary"
                  onClick={() => onBulkUnpublish(listElements)}
                >
                  {i18n.t("Unpublish")}
                </Button>
                <Button
                  color="primary"
                  onClick={() => onBulkPublish(listElements)}
                >
                  {i18n.t("Publish")}
                </Button>
                <IconButton
                  color="primary"
                  onClick={() => onBulkDelete(listElements)}
                >
                  <DeleteIcon />
                </IconButton>
              </>
            }
          >
            <TableRow>
              <TableCell />
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
                colSpan={4}
                hasNextPage={
                  pageInfo && !disabled ? pageInfo.hasNextPage : false
                }
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
                const isSelected = page ? isMember(page.id) : false;

                return (
                  <TableRow
                    hover={!!page}
                    className={!!page ? classes.link : undefined}
                    onClick={page ? onRowClick(page.id) : undefined}
                    key={page ? page.id : "skeleton"}
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
    );
  }
);
PageList.displayName = "PageList";
export default PageList;
