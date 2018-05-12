//
// Copyright 2006 Google Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// TODO(arv): Make sure no private fields are shown/or rename them.
// TODO(arv): Radial gradient
// TODO(arv): Clipping paths
// TODO(arv): Coordsize
// TODO(arv): Painting mode
// TODO(arv): Optimize
// TODO(arv): It looks like we need to modify the lineWidth slightly

function G_VmlCanvasManager() {
  this.init();
}

G_VmlCanvasManager.prototype = {
  init: function (opt_doc) {
    var doc = opt_doc || document;
    if (/MSIE/.test(navigator.userAgent) && !window.opera) {
      var self = this;
      doc.attachEvent("onreadystatechange", function () {
        self.init_(doc);
      });
    }
  },

  init_: function (doc, e) {
    if (doc.readyState == "complete") {
      // create xmlns
      if (!doc.namespaces["g_vml_"]) {
        doc.namespaces.add("g_vml_", "urn:schemas-microsoft-com:vml");
      }

      // setup default css
      var ss = doc.createStyleSheet();
      ss.cssText = "canvas{display:inline-block; overflow:hidden; text-align:left;}" +
          "canvas *{behavior:url(#default#VML)}";

      // find all canvas elements
      var els = doc.getElementsByTagName("canvas");
      for (var i = 0; i < els.length; i++) {
        if (!els[i].getContext) {
          this.initElement(els[i]);
        }
      }
    }
  },

  fixElement_: function (el) {
    // in IE before version 5.5 we would need to add HTML: to the tag name
    // but we do not care about IE before version 6
    var outerHTML = el.outerHTML;
    var newEl = document.createElement(outerHTML);
    // if the tag is still open IE has created the children as siblings and
    // it has also created a tag with the name "/FOO"
    if (outerHTML.slice(-2) != "/>") {
      var tagName = "/" + el.tagName;
      var ns;
      // remove content
      while ((ns = el.nextSibling) && ns.tagName != tagName) {
        ns.removeNode();
      }
      // remove the incorrect closing tag
      if (ns) {
        ns.removeNode();
      }
    }
    el.parentNode.replaceChild(newEl, el);
    return newEl;
  },

  initElement: function (el) {
    el = this.fixElement_(el);
    el.getContext = function () {
      if (this._context) {
        return this._context;
      }
      return this._context = new G_VmlCanvas(this);
    };

    var self = this; //bind
    el.attachEvent("onpropertychange", function (e) {
      // we need to watch changes to width and height
      switch (e.propertyName) {
        case "width":
        case "height":
          // coord size changed?
          break;
      }
    });

    // if style.height is set

    var attrs = el.attributes;
    if (attrs.width && attrs.width.specified) {
      // TODO: use runtimeStyle and coordsize
      // el.getContext().setWidth_(attrs.width.nodeValue);
      el.style.width = attrs.width.nodeValue + "px";
    }
    if (attrs.height && attrs.height.specified) {
      // TODO: use runtimeStyle and coordsize
      // el.getContext().setHeight_(attrs.height.nodeValue);
      el.style.height = attrs.height.nodeValue + "px";
    }
    //el.getContext().setCoordsize_()
  }
};

var G_vmlCanvasManager = new G_VmlCanvasMa