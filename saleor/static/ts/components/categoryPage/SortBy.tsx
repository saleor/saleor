import * as React from 'react';
import InlineSVG from 'react-inlinesvg';

let arrowUpIcon = require<string>('../../../images/arrow-up-icon.svg');
let arrowDownIcon = require<string>('../../../images/arrow-down-icon.svg');

interface SortByProps {
  setSorting(value: any): any;
  sortedValue?: string;
};

interface SortByState {
  visibility: boolean;
};

export default class SortBy extends React.Component<SortByProps, SortByState> {

  constructor(props) {
    super(props);
    this.state = {
      visibility: false
    };
  }

  setSorting = (event) => {
    const value = event.target.className;
    this.props.setSorting(value);
    this.changeVisibility();
  }

  changeVisibility = () => {
    this.setState({
      visibility: !this.state.visibility
    });
  }

  render() {
    const { sortedValue } = this.props;
    const { visibility } = this.state;
    return (
      <div className="sort-by">
        <div className={visibility ? ('click-area') : ('click-area hide')} onClick={this.changeVisibility}></div>
        <button className="btn btn-link" onClick={this.changeVisibility}>
          {sortedValue ? (
            sortedValue.search('-') ? (
              <div>
                <span>{gettext('Sort by:')} <strong>{sortedValue}</strong></span>
                <div className="sort-order-icon">
                  <InlineSVG key="arrowUpIcon" src={arrowUpIcon} />
                </div>
              </div>
            ) : (
               <div>
                <span>{gettext('Sort by:')} <strong>{sortedValue.replace('-', '')}</strong></span>
                <div className="sort-order-icon">
                  <InlineSVG key="arrowDownIcon" src={arrowDownIcon} />
                </div>
              </div>
            )
          ) : (
            <span>{gettext('Sort by:')} <strong>{gettext('default')}</strong></span>
          )}
        </button>
        {visibility && (
          <ul className="sort-list">
            <li className="name">
              <div className="row">
                <div className="col-md-6">{gettext('Sort by:')} <strong>{gettext('Name')}</strong></div>
                <div className="col-md-6">
                    <span className="name" onClick={this.setSorting}>{gettext('ascending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowUpIcon} />
                    </div>
                </div>
              </div>
              <div className="row">
                <div className="col-md-6"></div>
                <div className="col-md-6">
                    <span className="-name" onClick={this.setSorting}>{gettext('descending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowDownIcon} />
                    </div>
                </div>
              </div>
            </li>
            <li className="price">
              <div className="row">
                <div className="col-md-6">{gettext('Sort by:')} <strong>{gettext('Price')}</strong></div>
                <div className="col-md-6">
                    <span className="price" onClick={this.setSorting}>{gettext('ascending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowUpIcon} />
                    </div>
                </div>
              </div>
              <div className="row">
                <div className="col-md-6"></div>
                <div className="col-md-6">
                    <span className="-price" onClick={this.setSorting}>{gettext('descending')}</span>
                    <div className="float-right sort-order-icon">
                      <InlineSVG src={arrowDownIcon} />
                    </div>
                </div>
              </div>
            </li>
          </ul>
        )}
      </div>
    );
  }
}
