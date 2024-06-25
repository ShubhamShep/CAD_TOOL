import streamlit as st
import streamlit.components.v1 as components

# Define the HTML and JavaScript for the drawing canvas
html_code = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: Arial, sans-serif;
        }
        #buttonContainer {
            margin-bottom: 10px;
        }
        canvas {
            border: 1px solid black;
        }
    </style>
</head>
<body>
    <div id="buttonContainer">
        <button onclick="startDrawing()">Start Drawing</button>
        <button onclick="createPolygon()">Create Polygon</button>
        <button onclick="clearCanvas()">Clear Canvas</button>
        <button onclick="undo()">Undo</button>
        <button onclick="deletePolygon()">Delete Selected Polygon</button>
        <button onclick="saveAsPNG()">Save as PNG</button>
    </div>
    <canvas id="canvas" width="600" height="600"></canvas>
    <a id="downloadLink" style="display:none;"></a>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/4.5.0/fabric.min.js"></script>
    <script>
        const canvas = new fabric.Canvas('canvas');
        let points = [];
        let circles = [];
        let lines = [];
        let polygons = [];
        let texts = [];
        let sideLengths = [];
        let drawing = false;
        let tempLine = null;

        function startDrawing() {
            points = [];
            circles = [];
            lines = [];
            drawing = true;
            canvas.clear();
            drawGrid();
            addExistingElements();
        }

        function drawLine(x1, y1, x2, y2) {
            return new fabric.Line([x1, y1, x2, y2], { stroke: 'black' });
        }

        function addPoint(x, y) {
            points.push({ x, y });
            const circle = new fabric.Circle({
                left: x,
                top: y,
                radius: 5,
                fill: 'red',
                originX: 'center',
                originY: 'center'
            });
            circles.push(circle);
            canvas.add(circle);
        }

        function drawLines() {
            for (let i = 0; i < points.length - 1; i++) {
                const p1 = points[i];
                const p2 = points[i + 1];
                const line = drawLine(p1.x, p1.y, p2.x);
                lines.push(line);
                canvas.add(line);
            }
        }

        function promptLengthAndDrawLine() {
            const length = prompt("Enter the length of the side (feet):");
            if (length !== null && !isNaN(length)) {
                const lastPoint = points[points.length - 2];
                const newPoint = points[points.length - 1];
                const angle = Math.atan2(newPoint.y - lastPoint.y, newPoint.x - lastPoint.x);
                const x2 = lastPoint.x + length * Math.cos(angle);
                const y2 = lastPoint.y + length * Math.sin(angle);
                points[points.length - 1] = { x: x2, y: y2 };
                const line = drawLine(lastPoint.x, lastPoint.y, x2, y2);
                lines.push(line);
                canvas.add(line);
                canvas.remove(circles.pop());
                addPoint(x2, y2);
            } else {
                alert("Invalid length. Please enter a numeric value.");
            }
        }

        function onMouseMove(options) {
            if (!drawing || points.length === 0) return;

            const pointer = canvas.getPointer(options.e);
            const lastPoint = points[points.length - 1];
            if (tempLine) {
                canvas.remove(tempLine);
            }
            tempLine = drawLine(lastPoint.x, lastPoint.y, pointer.x, pointer.y);
            canvas.add(tempLine);
        }

        function onMouseDown(options) {
            if (!drawing) return;

            const pointer = canvas.getPointer(options.e);
            addPoint(pointer.x, pointer.y);

            if (points.length > 1) {
                promptLengthAndDrawLine();
            }

            if (tempLine) {
                canvas.remove(tempLine);
                tempLine = null;
            }
        }

        canvas.on('mouse:move', onMouseMove);
        canvas.on('mouse:down', onMouseDown);

        function createPolygon() {
            if (points.length > 2) {
                const lastPoint = points[points.length - 1];
                const firstPoint = points[0];
                const line = drawLine(lastPoint.x, lastPoint.y, firstPoint.x, firstPoint.y);
                lines.push(line);
                canvas.add(line);

                const polygon = new fabric.Polygon(points, { stroke: 'blue', fill: ' Light Yellow', selectable: true });
                polygons.push(polygon);
                canvas.add(polygon);

                const name = prompt("Enter a name for the polygon:");
                const area = calculatePolygonArea(points);
                const centroid = calculateCentroid(points);
                const text = new fabric.Text(`${name}\nArea: ${area.toFixed(2)} sq ft`, {
                    left: centroid.x,
                    top: centroid.y,
                    fontSize: 16,
                    fill: 'black',
                    originX: 'center',
                    originY: 'center'
                });
                texts.push(text);
                canvas.add(text);

                // Add side lengths
                addSideLengths(points);

                points = [];
                circles.forEach(circle => canvas.remove(circle));
                lines.forEach(line => canvas.remove(line));
                circles = [];
                lines = [];
                drawing = false;
            } else {
                alert("A polygon requires at least 3 points.");
            }
        }

        function calculatePolygonArea(points) {
            let area = 0;
            for (let i = 0; i < points.length; i++) {
                const j = (i + 1) % points.length;
                area += points[i].x * points[j].y;
                area -= points[j].x * points[i].y;
            }
            return Math.abs(area / 2);
        }

        function calculateCentroid(points) {
            let x = 0, y = 0;
            for (let i = 0; i < points.length; i++) {
                x += points[i].x;
                y += points[i].y;
            }
            return { x: x / points.length, y: y / points.length };
        }

        function addSideLengths(points) {
            for (let i = 0; i < points.length; i++) {
                const j = (i + 1) % points.length;
                const p1 = points[i];
                const p2 = points[j];
                const length = calculateDistance(p1, p2).toFixed(2);
                const midpoint = calculateMidpoint(p1, p2);
                const text = new fabric.Text(length + " ft", {
                    left: midpoint.x,
                    top: midpoint.y,
                    fontSize: 14,
                    fill: 'black',
                    originX: 'center',
                    originY: 'center'
                });
                sideLengths.push(text);
                canvas.add(text);
            }
        }

        function calculateDistance(p1, p2) {
            return Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2));
        }

        function calculateMidpoint(p1, p2) {
            return { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 };
        }

        function clearCanvas() {
            canvas.clear();
            points = [];
            circles = [];
            lines = [];
            drawing = false;
            drawGrid();
            addExistingElements();
        }

        function undo() {
            if (points.length > 0) {
                points.pop();
                const lastCircle = circles.pop();
                if (lastCircle) {
                    canvas.remove(lastCircle);
                }
                const lastLine = lines.pop();
                if (lastLine) {
                    canvas.remove(lastLine);
                }
            }
        }

        function drawGrid() {
            const gridSize = 10;
            const width = canvas.getWidth();
            const height = canvas.getHeight();
            for (let i = 0; i < width; i += gridSize) {
                canvas.add(new fabric.Line([i, 0, i, height], { stroke: '#ddd', selectable: false }));
                canvas.add(new fabric.Line([0, i, width, i], { stroke: '#ddd', selectable: false }));
            }
        }

        function addExistingElements() {
            polygons.forEach(polygon => canvas.add(polygon));
            texts.forEach(text => canvas.add(text));
            sideLengths.forEach(text => canvas.add(text));
        }

        function deletePolygon() {
            const activeObject = canvas.getActiveObject();
            if (activeObject && activeObject.type === 'polygon') {
                // Remove the polygon
                canvas.remove(activeObject);
                
                // Find and remove the associated text and side lengths
                const index = polygons.indexOf(activeObject);
                if (index !== -1) {
                    const text = texts[index];
                    const lengthTexts = sideLengths.slice(index * points.length, (index + 1) * points.length);
                    canvas.remove(text);
                    lengthTexts.forEach(text => canvas.remove(text));

                    polygons.splice(index, 1);
                    texts.splice(index, 1);
                    sideLengths.splice(index * points.length, points.length);
                }
            }
        }

        function saveAsPNG() {
            // Set canvas background to white
            const background = new fabric.Rect({
                left: 0,
                top: 0,
                width: canvas.getWidth(),
                height: canvas.getHeight(),
                fill: 'white',
                selectable: false
            });
            canvas.add(background);
            canvas.sendToBack(background);

            // Save canvas as PNG
            const dataURL = canvas.toDataURL({ format: 'png' });
            const link = document.getElementById('downloadLink');
            link.href = dataURL;
            link.download = 'canvas.png';
            link.click();

            // Remove the background after saving
            canvas.remove(background);
        }

        drawGrid();
    </script>
</body>
</html>
"""

# Render the HTML and JavaScript in the Streamlit app
components.html(html_code, height=700)
