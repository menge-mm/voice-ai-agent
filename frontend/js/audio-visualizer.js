/**
 * Audio Visualizer
 * Real-time audio waveform visualization
 */

export class AudioVisualizer {
    constructor(canvasElement) {
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        this.analyser = null;
        this.dataArray = null;
        this.animationId = null;
        this.isRunning = false;
    }

    start(stream) {
        if (this.isRunning) {
            console.warn('Visualizer already running');
            return;
        }

        try {
            const audioContext = new AudioContext();
            const source = audioContext.createMediaStreamSource(stream);

            this.analyser = audioContext.createAnalyser();
            this.analyser.fftSize = 2048;

            source.connect(this.analyser);

            const bufferLength = this.analyser.frequencyBinCount;
            this.dataArray = new Uint8Array(bufferLength);

            this.isRunning = true;
            this.draw();

            console.log('✓ Audio visualizer started');
        } catch (error) {
            console.error('✗ Failed to start visualizer:', error);
        }
    }

    draw() {
        if (!this.isRunning) return;

        this.animationId = requestAnimationFrame(() => this.draw());

        this.analyser.getByteTimeDomainData(this.dataArray);

        // Clear canvas
        this.ctx.fillStyle = 'rgb(249, 250, 251)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Draw waveform
        this.ctx.lineWidth = 2;
        this.ctx.strokeStyle = 'rgb(59, 130, 246)'; // Blue color
        this.ctx.beginPath();

        const sliceWidth = this.canvas.width / this.dataArray.length;
        let x = 0;

        for (let i = 0; i < this.dataArray.length; i++) {
            const v = this.dataArray[i] / 128.0;
            const y = (v * this.canvas.height) / 2;

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        this.ctx.lineTo(this.canvas.width, this.canvas.height / 2);
        this.ctx.stroke();
    }

    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }

        this.isRunning = false;

        // Clear canvas
        if (this.ctx) {
            this.ctx.fillStyle = 'rgb(249, 250, 251)';
            this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        }

        console.log('✓ Audio visualizer stopped');
    }
}

export default AudioVisualizer;
