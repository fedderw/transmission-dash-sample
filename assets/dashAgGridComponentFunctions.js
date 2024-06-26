var dagcomponentfuncs = (window.dashAgGridComponentFunctions =
  window.dashAgGridComponentFunctions || {})

// use for making dbc.Button with FontAwesome or Bootstrap icons
dagcomponentfuncs.DBC_Button = function (props) {
  const { setData, data } = props

  function onClick () {
    setData()
  }
  let leftIcon, rightIcon
  if (props.leftIcon) {
    leftIcon = React.createElement('i', {
      className: props.leftIcon
    })
  }
  if (props.rightIcon) {
    rightIcon = React.createElement('i', {
      className: props.rightIcon
    })
  }
  return React.createElement(
    window.dash_bootstrap_components.Button,
    {
      onClick,
      color: props.color,
      disabled: props.disabled,
      download: props.download,
      external_link: props.external_link,
      // change this link for your application:
      href:
        props.href === undefined
          ? null
          : 'https://finance.yahoo.com/quote/' + props.value,
      outline: props.outline,
      size: props.size,
      style: {
        margin: props.margin,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      },
      target: props.target,
      title: props.title,
      type: props.type
    },
    leftIcon,
    props.value,
    rightIcon
  )
}

dagcomponentfuncs.CustomButtonRenderer = function (params) {
  var button = document.createElement('button')
  button.textContent = 'Details'
  button.addEventListener('click', function () {
    params.api.dispatchEvent({
      type: 'cellClicked',
      event: event,
      node: params.node,
      column: params.column,
      colDef: params.colDef,
      data: params.data,
      rowIndex: params.rowIndex,
      api: params.api,
      columnApi: params.columnApi,
      context: params.context,
      value: params.value
    })
  })
  return button
}

function linkRenderer(params) {
  return '<a href="' + params.value + '" target="_blank">' + params.value + '</a>';
}
