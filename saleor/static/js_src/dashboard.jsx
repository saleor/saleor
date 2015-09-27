import React from "react";
import Griddle from "griddle-react";

class DataTable extends React.Component {
    state = {
        rows: [],
        sortColumn: this.props.defaultSortColumn,
        defaultSort: this.props.defaultSort,
        sortAscending: this.props.defaultSort == "asc",
        currentPage: 0,
        maxPage: 0,
        tableClassName: this.props.tableClassName
    };

    componentDidMount() {
        this.getRows();
    }

    getRows(sortColumn, sortAscending, newPage) {
        var sortColumn = sortColumn !== undefined ? sortColumn : this.state.sortColumn;
        var sortAscending = sortAscending !== undefined ? sortAscending : this.state.sortAscending;
        var newPage = newPage !== undefined ? newPage : this.state.currentPage;

        var ordering = (sortAscending ? "" : "-") + sortColumn;
        var that = this;
        var timeout;

        $.ajax({
            url: this.props.apiUrl,
            method: "get",
            data: {
                ordering: ordering,
                page: newPage + 1,
                page_size: this.props.pageSize
            },
            dataType: "json",
            beforeSend: function() {
                that.props.classNameBackup = that.state.tableClassName;

                timeout = setTimeout(function() {
                    that.setState({
                        tableClassName: that.state.tableClassName + " data-table--loading"
                    });
                }, 200);
            },
            success: function (data) {
                window.clearTimeout(timeout);

                that.setState({
                    rows: data.results,
                    sortColumn: sortColumn,
                    sortAscending: sortAscending,
                    currentPage: newPage,
                    maxPage: Math.ceil(data.count / that.props.pageSize),
                    tableClassName: that.props.classNameBackup
                });
            }
        });
    }

    changeSort(sortColumn, sortAscending) {
        this.getRows(sortColumn, sortAscending, this.state.externalCurrentPage);
    }

    setPage(page) {
        this.getRows(this.state.externalSortColumn, this.state.externalSortAscending, page);
    }

    render() {
        return <Griddle
            useExternal={true}
            results={this.state.rows}
            columns={this.props.columns}
            columnMetadata={this.props.columnMetadata}
            externalSortColumn={this.state.sortColumn}
            externalSortAscending={this.state.sortAscending}
            externalMaxPage={this.state.maxPage}
            externalCurrentPage={this.state.currentPage}
            externalSetFilter
            externalChangeSort={::this.changeSort}
            externalSetPage={::this.setPage}
            externalSetPageSize
            useGriddleStyles={false}
            tableClassName={this.state.tableClassName}
            sortAscendingComponent={<span className="data-table--orderable-ascending"></span>}
            sortDescendingComponent={<span className="data-table--orderable-descending"></span>}
            useCustomPagerComponent={true}
            customPagerComponent={OtherPager}
            noDataMessage={this.props.noDataMessage}
        />;
    };
}

var OtherPager = React.createClass({
    getDefaultProps: function(){
        return {
            "maxPage": 0,
            "nextText": "",
            "previousText": "",
            "currentPage": 0
        }
    },
    pageChange: function(event){
        this.props.setPage(parseInt(event.target.getAttribute("data-value")));
    },
    render: function(){
        return (
            <div className="data-table-pagination">
                <ul>
                    <li className={this.props.currentPage ? "" : "data-table-pagination-inactive"}>
                        <i data-value="0" onClick={this.pageChange} className="data-table-pagination-prev"></i>
                    </li>
                    <li className={this.props.currentPage ? "" : "data-table-pagination-inactive"}>
                        <i onClick={this.props.previous} className="data-table-pagination-prev"></i>
                    </li>
                    <li className={this.props.currentPage != (this.props.maxPage -1) ? "" : "data-table-pagination-inactive"}>
                        <i onClick={this.props.next} className="data-table-pagination-next"></i>
                    </li>
                    <li className={this.props.currentPage != (this.props.maxPage - 1) ? "" : "data-table-pagination-inactive"}>
                        <i data-value={this.props.maxPage - 1} onClick={this.pageChange} className="data-table-pagination-next"></i>
                    </li>
                </ul>
            </div>
        )
    }
});

class OrderLink extends React.Component {
    render() {
        return <a href={this.props.data}>
            #{this.props.data}
        </a>;
    };
}

class OrderStatus extends React.Component {
    render() {
        return <Label text={this.props.rowData.status_display}
            classSuffix={this.props.rowData.status_css_class} />
    }
}

class OrderLastPaymentStatus extends React.Component {
    render() {
        return <Label text={this.props.rowData.last_payment_status_display}
            classSuffix={this.props.rowData.last_payment_css_class} />;
    }
}

class CustomerEmail extends React.Component {
    render() {
        return <a href={this.props.rowData.dashboard_customer_url}>
            {this.props.data}
        </a>;
    };
}

class CustomerLastOrder extends React.Component {
    render() {
        return <a href={this.props.rowData.dashboard_last_order_url}>
            #{this.props.data}
        </a>;
    };
}

class CustomerFullname extends React.Component {
    render() {
        return <span>
            {this.props.data} {this.props.rowData.default_shipping_address__first_name}
        </span>;
    }
}

class CustomerLocation extends React.Component {
    render() {
        return <span>
            {this.props.data}, {this.props.rowData.default_shipping_address__city}
        </span>;
    }
}

class Label extends React.Component {
    render() {
        var className = "data-table-status--" + this.props.classSuffix;
        return <span className={className}>{this.props.text}</span>;
    }
}

var customComponents = {
    "CustomerEmail": CustomerEmail,
    "CustomerFullname": CustomerFullname,
    "CustomerLastOrder": CustomerLastOrder,
    "CustomerLocation": CustomerLocation,
    "OrderLastPaymentStatus": OrderLastPaymentStatus,
    "OrderLink": OrderLink,
    "OrderStatus": OrderStatus
};

$(".data-table--orderable").each(function() {
    var columns = [];
    var columnMetadata = [];

    $(this).find("th").each(function() {
        var columnName = $(this).data("key") ? $(this).data("key") : this.innerText.toLowerCase().split(" ").join("_");
        columns.push(columnName);
        columnMetadata.push({
            columnName: columnName,
            displayName: this.innerText,
            customComponent: customComponents[$(this).data("component")] ? customComponents[$(this).data("component")] : undefined,
            cssClassName: $(this).data("css-class")
        });
    });

    var props = {
        apiUrl: $(this).data("table-api"),
        defaultSortColumn: $(this).data("default-sort-column") ? $(this).data("default-sort-column") : "id",
        defaultSort: $(this).data("default-sort") ? $(this).data("default-sort") : "asc",
        columns: columns,
        columnMetadata: columnMetadata,
        pageSize: $(this).data("page-size") ? $(this).data("page-size") : 10,
        noDataMessage: $(this).data("no-data-message"),
        tableClassName: $(this).attr("class")
    };
    React.render(<DataTable {...props} />, this.parentElement);
});
