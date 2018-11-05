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
import Typography from "@material-ui/core/Typography";
import * as classNames from "classnames";
import * as React from "react";

import Skeleton from "../../../components/Skeleton";
import TablePagination from "../../../components/TablePagination";
import i18n from "../../../i18n";
import { maybe, renderCollection } from "../../../misc";
import { ListProps } from "../../../types";
import { StaffList_staffUsers_edges_node } from "../../types/StaffList";

const styles = (theme: Theme) =>
  createStyles({
    avatar: {
      alignItems: "center",
      backgroundColor: theme.palette.primary.main,
      borderRadius: "100%",
      display: "grid",
      float: "left",
      height: 37,
      justifyContent: "center",
      marginRight: theme.spacing.unit * 1 + "px",
      width: 37
    },
    avatarText: {
      color: "#ffffff",
      fontSize: 18,
      pointerEvents: "none"
    },
    statusText: {
      color: "#9E9D9D"
    },
    tableRow: {
      cursor: "pointer"
    },
    wideColumn: {
      width: "80%"
    }
  });

interface StaffListProps extends ListProps, WithStyles<typeof styles> {
  staffMembers: StaffList_staffUsers_edges_node[];
}

const StaffList = withStyles(styles, { name: "StaffList" })(
  ({
    classes,
    disabled,
    onNextPage,
    onPreviousPage,
    onRowClick,
    pageInfo,
    staffMembers
  }: StaffListProps) => (
    <Card>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell className={classes.wideColumn}>
              {i18n.t("Name", { context: "object" })}
            </TableCell>
            <TableCell>
              {i18n.t("Email Address", { context: "object" })}
            </TableCell>
          </TableRow>
        </TableHead>
        <TableFooter>
          <TableRow>
            <TablePagination
              colSpan={3}
              hasNextPage={
                pageInfo && !disabled ? pageInfo.hasNextPage : undefined
              }
              onNextPage={onNextPage}
              hasPreviousPage={
                pageInfo && !disabled ? pageInfo.hasPreviousPage : undefined
              }
              onPreviousPage={onPreviousPage}
            />
          </TableRow>
        </TableFooter>
        <TableBody>
          {renderCollection(
            staffMembers,
            staffMember => (
              <TableRow
                className={classNames({
                  [classes.tableRow]: !!staffMember
                })}
                hover={!!staffMember}
                onClick={!!staffMember ? onRowClick(staffMember.id) : undefined}
                key={staffMember ? staffMember.id : "skeleton"}
              >
                <TableCell>
                  {staffMember &&
                  staffMember.firstName &&
                  staffMember.lastName !== undefined ? (
                    <>
                      <div className={classes.avatar}>
                        <Typography className={classes.avatarText}>
                          {maybe(
                            () =>
                              `${staffMember.firstName[0].toUpperCase()}${staffMember.lastName[0].toUpperCase()}`
                          ) || ""}
                        </Typography>
                      </div>
                      <Typography>
                        {`${staffMember.firstName} ${staffMember.lastName}`}
                      </Typography>
                      <Typography
                        variant={"caption"}
                        className={classes.statusText}
                      >
                        {staffMember.isActive
                          ? i18n.t("Active", { context: "status" })
                          : i18n.t("Inactive", { context: "status" })}
                      </Typography>
                    </>
                  ) : (
                    <Skeleton style={{ width: "10em" }} />
                  )}
                </TableCell>
                <TableCell>
                  {staffMember ? (
                    <span onClick={onRowClick(staffMember.id)}>
                      {staffMember.email}
                    </span>
                  ) : (
                    <Skeleton />
                  )}
                </TableCell>
              </TableRow>
            ),
            () => (
              <TableRow>
                <TableCell colSpan={2}>
                  {i18n.t("No staff members found")}
                </TableCell>
              </TableRow>
            )
          )}
        </TableBody>
      </Table>
    </Card>
  )
);
StaffList.displayName = "StaffList";
export default StaffList;
